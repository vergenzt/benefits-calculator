from decimal import Decimal
import json
import math
import pickle
from typing import Any, Callable, Dict, Iterator, List, Optional, TypedDict
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


to_str: Callable[[List[Tx]], str]
to_txs: Callable[[str], List[Tx]]
to_str, to_txs = (  # type: ignore
    lambda txs: urlsafe_b64encode(pickle.dumps(txs)).decode().rstrip("="),
    lambda txq: pickle.loads(urlsafe_b64decode(txq + "==")),
)


st.header("Expected Expenses")

txs_initial = [new_tx({"desc": "Monthly Premium"})]

txs_key = "txs"
txs: List[Tx] = to_txs(txq) if (txq := st.query_params.get(txs_key)) else txs_initial


def data_update():
    match st.session_state[editor_key]:
        case {"added_rows": [row]}:
            txs.append(row)
        case {"deleted_rows": [i]}:
            txs.pop(i)
        case {"edited_rows": edit}:
            i, row = edit.popitem()
            txs[i].update(row)

    st.query_params.update({txs_key: to_str(txs)})
    st.session_state.update({"gen": gen + 1})


st.data_editor(
    txs,
    num_rows="dynamic",
    use_container_width=True,
    key=(editor_key := f"data_editor.{(gen := st.session_state.setdefault("gen", 0))}"),
    on_change=data_update,
)


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
