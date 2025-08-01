use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyTuple};
use std::collections::HashMap;

/// Count adjacent byte pairs from a list of (pretokens, count) pairs
#[pyfunction]
fn count_adjacent_pairs(py: Python, input: Vec<(Vec<Vec<u8>>, usize)>) -> Py<PyAny> {
    let mut pair_counts: HashMap<(Vec<u8>, Vec<u8>), usize> = HashMap::new();

    for (token_tuple, count) in input {
        if token_tuple.len() < 2 {
            continue;
        }
        for i in 0..(token_tuple.len() - 1) {
            let pair = (token_tuple[i].clone(), token_tuple[i + 1].clone());
            *pair_counts.entry(pair).or_insert(0) += count;
        }
    }

    // Convert result back to Python dict of (tuple(bytes, bytes)) → int
    let py_dict = pyo3::types::PyDict::new(py);
    for ((a, b), count) in pair_counts {
        let a_bytes = PyBytes::new(py, &a);
        let b_bytes = PyBytes::new(py, &b);
        let key = PyTuple::new(py, &[a_bytes, b_bytes]);
        py_dict.set_item(key, count).unwrap();
    }

    py_dict.into()
}


/// This is the module entrypoint for Python
#[pymodule]
fn rust_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(count_adjacent_pairs, m)?)?;
    Ok(())
}