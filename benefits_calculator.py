from decimal import Decimal
import json
import math
import pickle
from typing import Any, Callable, Iterator, Optional, TypedDict
from datetime import date, timedelta
from base64 import urlsafe_b64encode, urlsafe_b64decode

import streamlit as st


class PartialTx(TypedDict, total=False):
    desc: str
    date: date
    ded: bool
    oop: bool
    ppo: Decimal
    hdhp: Decimal
    freq: Optional[int]
    freq_weekly: bool
    freq_num: Optional[int]


class Tx(PartialTx, TypedDict):
    pass


def new_tx(old_tx: PartialTx) -> Tx:
    return {
        "desc": "",
        "date": date(2025, 1, 1),
        "ded": False,
        "oop": False,
        "ppo": Decimal(0),
        "hdhp": Decimal(0),
        "freq": 1,
        "freq_weekly": False,
        "freq_num": None,
        **old_tx,
    }


class Serde:
    @staticmethod
    def des(txq: str) -> Any:
        return pickle.loads(urlsafe_b64decode(txq))

    @staticmethod
    def ser(txs: Any) -> str:
        return urlsafe_b64encode(pickle.dumps(txs)).decode()


st.header("Expected Expenses")

txs_key = "txs"
txs_initial = (
    Serde.des(txq)
    if (txq := st.query_params.get(txs_key))
    else [new_tx({"desc": "Monthly Premium"})]
)
txs = st.data_editor(
    txs_initial,
    num_rows="dynamic",
    use_container_width=True,
)

st.query_params.update({ txs_key: Serde.ser(txs) })


def get_instances(tx: Tx) -> Iterator[Tx]:
    if (txdt := tx.get("date")) and (freq := tx.get("freq")) and not math.isnan(freq):
        yield tx
        while txdt < date(2026, 1, 1):
            if tx.get("freq_weekly"):
                txdt += timedelta(weeks=freq)
            else:
                txdt = date(
                    txdt.year + int(txdt.month / 12),
                    ((txdt.month % 12) + int(freq)),
                    txdt.day,
                )
            yield new_tx({**tx, "date": txdt})


tx_instances = st.dataframe(
    sorted(
        [tx_inst for tx in txs for tx_inst in get_instances(tx)],
        key=lambda x: x.get("date"),
    ),
    use_container_width=True,
    height=800,
)

st.session_state
