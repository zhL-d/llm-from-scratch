import pandas as pd
from rich.table import Table
from rich.console import Console

a = [(b'b', b'e'), (b' ', b't'), (b' ', b'a'), (b' t', b'h'), (b' ', b's'), (b' ', b'w'), (b'n', b'd'), (b' t', b'he'), (b'e', b'd'), (b' ', b'b'), (b' t', b'o'), (b'a', b'nd'), (b' a', b'nd'), (b' ', b'h'), (b' ', b'f'), (b'i', b'n'), (b' w', b'a'), (b' ', b'T'), (b'i', b't'), (b'r', b'e'), (b'o', b'u'), (b' ', b'l'), (b' ', b'd'), (b' ', b'c'), (b' ', b'p'), (b'a', b'y'), (b' wa', b's'), (b' ', b'm'), (b'o', b'm'), (b' T', b'h'), (b' ', b'he'), (b' T', b'he'), (b'i', b's'), (b' ', b'n'), (b'o', b'n'), (b'i', b'm'), (b'l', b'l'), (b' s', b'a'), (b'i', b'd'), (b'v', b'e'), (b' h', b'a'), (b' ', b'g'), (b' ', b'S'), (b'a', b't'), (b'in', b'g'), (b'o', b't'), (b'a', b'r'), (b'n', b't'), (b'o', b'r'), (b'l', b'e'), (b'i', b'r'), (b'H', b'e'), (b'a', b'm'), (b' ', b'it'), (b' l', b'i'), (b' ', b'He'), (b'r', b'y'), (b'i', b'g'), (b'e', b't'), (b'e', b're'), (b' The', b'y'), (b' ', b'in'), (b'a', b'll'), (b' p', b'l'), (b' pl', b'a'), (b' ', b'"'), (b'o', b'w'), (b' s', b'h'), (b'h', b'is'), (b' b', b'e'), (b'd', b'ay'), (b'l', b'y'), (b' ', b'u'), (b'u', b't'), (b'a', b'id'), (b'it', b'h'), (b' d', b'ay'), (b's', b'aid'), (b' sa', b'id'), (b'p', b'p'), (b' pl', b'ay'), (b'O', b'n'), (b'w', b'ith'), (b' w', b'ith'), (b' he', b'r'), (b'r', b'i'), (b' ', b'o'), (b' ', b'y'), (b'T', b'im'), (b'o', b'o'), (b'k', b'ed'), (b'l', b'd'), (b' ', b'e'), (b'c', b'e'), (b'ri', b'e'), (b'h', b'at'), (b'k', b'e'), (b'am', b'e'), (b' S', b'h'), (b' h', b'is'), (b' S', b'he'), (b' ', b'I'), (b' s', b't'), (b' T', b'im'), (b'a', b'pp'), (b'e', b'ry'), (b'b', b'ig'), (b' b', b'ig'), (b' y', b'o'), (b've', b'ry'), (b' y', b'ou'), (b's', b't'), (b' ', b'r'), (b'a', b'nt'), (b'h', b'app'), (b' ha', b'pp'), (b' ', b'on'), (b' m', b'a'), (b'i', b'ly'), (b'rie', b'n'), (b'rie', b'nd'), (b'n', b'ot'), (b'f', b'riend'), (b'f', b'rien'), (b' f', b'riend'), (b' f', b'rien'), (b' ', b'L'), (b'f', b'or'), (b'a', b're'), (b'c', b'k'), (b' u', b'p'), (b' the', b'y'), (b'w', b'ant'), (b' wa', b'nt'), (b' ha', b'd'), (b' n', b'ot'), (b'it', b't'), (b' o', b'f'), (b' ', b'B'), (b' f', b'or'), (b'e', b'nt'), (b'happ', b'y'), (b' happ', b'y'), (b' ', b'M'), (b' d', b'o'), (b' ', b'very'), (b't', b'hat'), (b' th', b'at'), (b'he', b're'), (b'On', b'e'), (b' sa', b'w'), (b'm', b'om'), (b' m', b'om'), (b'u', b'ld'), (b'ou', b'ld'), (b"'", b's'), (b'itt', b'le'), (b'itt', b'l'), (b'im', b'e'), (b'l', b'ittle'), (b'l', b'ittl'), (b'T', b'om'), (b' l', b'ittle'), (b' l', b'ittl'), (b't', b'ime'), (b' s', b'he'), (b'id', b'e'), (b's', b'e'), (b'n', b'ce'), (b' t', b'ime'), (b' ', b'k'), (b' n', b'e'), (b'n', b'ame'), (b' L', b'i'), (b'et', b'h'), (b' n', b'ame'), (b' s', b'o'), (b' c', b'o'), (b't', b'here'), (b'am', b'ed'), (b' the', b're'), (b'ou', b'n'), (b' Li', b'l'), (b'.', b'"'), (b'ou', b'nd'), (b'c', b'ar'), (b' b', b'o'), (b' L', b'ily'), (b'ir', b'd'), (b' s', b'm'), (b'want', b'ed'), (b'want', b'e'), (b' want', b'ed'), (b' want', b'e'), (b'b', b'ird'), (b' b', b'ird'), (b' T', b'om'), (b'w', b'ere'), (b' ', b're'), (b'v', b'ed'), (b'l', b'oo'), (b' w', b'ere'), (b'a', b'd'), (b'h', b'ad'), (b'b', b'ut'), (b' b', b'ut'), (b'friend', b's'), (b' friend', b's'), (b'!', b'"'), (b'ou', b't'), (b'c', b'h'), (b'i', b'ke'), (b' l', b'o'), (b'h', b't'), (b'g', b'ht'), (b'T', b'he'), (b'The', b'y'), (b'l', b'p'), (b'l', b'ike'), (b' li', b'ke'), (b' to', b'o'), (b'e', b'lp'), (b't', b'oo'), (b' w', b'h'), (b'r', b'a'), (b'On', b'ce'), (b'he', b'lp'), (b' he', b'lp'), (b' f', b'u'), (b'w', b'ent'), (b' w', b'ent'), (b' a', b'll'), (b' I', b't'), (b' ', b'A'), (b'u', b'e'), (b' a', b'n'), (b' f', b'e'), (b're', b'e'), (b' l', b'oo'), (b'loo', b'k'), (b' ', b'is'), (b' loo', b'k'), (b' up', b'on')]
b = [(b'h', b'e'), (b' ', b't'), (b' ', b'a'), (b' t', b'h'), (b' ', b's'), (b' ', b'w'), (b'n', b'd'), (b' t', b'he'), (b'e', b'd'), (b' ', b'b'), (b' t', b'o'), (b'a', b'nd'), (b' a', b'nd'), (b' ', b'h'), (b' ', b'f'), (b'i', b'n'), (b' w', b'a'), (b' ', b'T'), (b'i', b't'), (b'r', b'e'), (b'o', b'u'), (b' ', b'l'), (b' ', b'd'), (b' ', b'c'), (b' ', b'p'), (b'a', b'y'), (b' wa', b's'), (b' ', b'm'), (b'o', b'm'), (b' T', b'h'), (b' ', b'he'), (b' T', b'he'), (b'i', b's'), (b' ', b'n'), (b'o', b'n'), (b'i', b'm'), (b'l', b'l'), (b' s', b'a'), (b'i', b'd'), (b'v', b'e'), (b' h', b'a'), (b' ', b'g'), (b' ', b'S'), (b'a', b't'), (b'in', b'g'), (b'o', b't'), (b'a', b'r'), (b'n', b't'), (b'o', b'r'), (b'l', b'e'), (b'i', b'r'), (b'H', b'e'), (b'a', b'm'), (b' ', b'it'), (b' l', b'i'), (b' ', b'He'), (b'r', b'y'), (b'i', b'g'), (b'e', b't'), (b'e', b're'), (b' The', b'y'), (b' ', b'in'), (b'a', b'll'), (b' p', b'l'), (b' pl', b'a'), (b' ', b'"'), (b'o', b'w'), (b' s', b'h'), (b'h', b'is'), (b' b', b'e'), (b'd', b'ay'), (b'l', b'y'), (b' ', b'u'), (b'u', b't'), (b'a', b'id'), (b'it', b'h'), (b' d', b'ay'), (b's', b'aid'), (b' sa', b'id'), (b'p', b'p'), (b' pl', b'ay'), (b'O', b'n'), (b'w', b'ith'), (b' w', b'ith'), (b' he', b'r'), (b'r', b'i'), (b' ', b'o'), (b' ', b'y'), (b'T', b'im'), (b'o', b'o'), (b'k', b'ed'), (b'l', b'd'), (b' ', b'e'), (b'c', b'e'), (b'ri', b'e'), (b'h', b'at'), (b'k', b'e'), (b'am', b'e'), (b' S', b'h'), (b' h', b'is'), (b' S', b'he'), (b' ', b'I'), (b' s', b't'), (b' T', b'im'), (b'a', b'pp'), (b'e', b'ry'), (b'b', b'ig'), (b' b', b'ig'), (b' y', b'o'), (b've', b'ry'), (b' y', b'ou'), (b's', b't'), (b' ', b'r'), (b'a', b'nt'), (b'h', b'app'), (b' ha', b'pp'), (b' ', b'on'), (b' m', b'a'), (b'i', b'ly'), (b'rie', b'n'), (b'rie', b'nd'), (b'n', b'ot'), (b'f', b'riend'), (b'f', b'rien'), (b' f', b'riend'), (b' f', b'rien'), (b' ', b'L'), (b'f', b'or'), (b'a', b're'), (b'c', b'k'), (b' u', b'p'), (b' the', b'y'), (b'w', b'ant'), (b' wa', b'nt'), (b' ha', b'd'), (b' n', b'ot'), (b'it', b't'), (b' o', b'f'), (b' ', b'B'), (b' f', b'or'), (b'e', b'nt'), (b'happ', b'y'), (b' happ', b'y'), (b' ', b'M'), (b' d', b'o'), (b' ', b'very'), (b't', b'hat'), (b' th', b'at'), (b'he', b're'), (b'On', b'e'), (b' sa', b'w'), (b'm', b'om'), (b' m', b'om'), (b'u', b'ld'), (b'ou', b'ld'), (b"'", b's'), (b'itt', b'le'), (b'itt', b'l'), (b'im', b'e'), (b'l', b'ittle'), (b'l', b'ittl'), (b'T', b'om'), (b' l', b'ittle'), (b' l', b'ittl'), (b't', b'ime'), (b' s', b'he'), (b'id', b'e'), (b's', b'e'), (b'n', b'ce'), (b' t', b'ime'), (b' ', b'k'), (b' n', b'e'), (b'n', b'ame'), (b' L', b'i'), (b'et', b'h'), (b' n', b'ame'), (b' s', b'o'), (b' c', b'o'), (b't', b'here'), (b'am', b'ed'), (b' the', b're'), (b'ou', b'n'), (b' Li', b'l'), (b'.', b'"'), (b'ou', b'nd'), (b'c', b'ar'), (b' b', b'o'), (b' L', b'ily'), (b'ir', b'd'), (b' s', b'm'), (b'want', b'ed'), (b'want', b'e'), (b' want', b'ed'), (b' want', b'e'), (b'b', b'ird'), (b' b', b'ird'), (b' T', b'om'), (b'w', b'ere'), (b' ', b're'), (b'v', b'ed'), (b'l', b'oo'), (b' w', b'ere'), (b'a', b'd'), (b'h', b'ad'), (b'b', b'ut'), (b' b', b'ut'), (b'friend', b's'), (b' friend', b's'), (b'!', b'"'), (b'ou', b't'), (b'c', b'h'), (b'i', b'ke'), (b' l', b'o'), (b'h', b't'), (b'g', b'ht'), (b'T', b'he'), (b'The', b'y'), (b'l', b'p'), (b'l', b'ike'), (b' li', b'ke'), (b' to', b'o'), (b'e', b'lp'), (b't', b'oo'), (b' w', b'h'), (b'r', b'a'), (b'On', b'ce'), (b'he', b'lp'), (b' he', b'lp'), (b' f', b'u'), (b'w', b'ent'), (b' w', b'ent'), (b' a', b'll'), (b' I', b't'), (b' ', b'A'), (b'u', b'e'), (b' a', b'n'), (b' f', b'e'), (b're', b'e'), (b' l', b'oo'), (b'loo', b'k'), (b' ', b'is'), (b' loo', b'k'), (b' up', b'on')]


# Turn each into a DataFrame with a simple integer index
df_a = pd.DataFrame({"A": a})
df_b = pd.DataFrame({"B": b})

# Perform a full outer join on the integer index so we keep every row
df = pd.concat([df_a, df_b], axis=1)

# If one list is shorter, missing entries become NaN; fill with a sentinel if you like:
df = df.fillna("<MISSING>")

# Now df looks like:
#                    A                 B
# 0         (b'b', b'e')       (b'h', b'e')
# 1         (b' ', b't')       (b' ', b't')
# 2         (b' ', b'a')       (b' ', b'a')
# 3         (b' t', b'h')      (b' t', b'h')
# 4         (b' ', b's')       (b' ', b's')
# …

console = Console()
table = Table(show_header=True, header_style="bold magenta")
table.add_column("Row", justify="right")
table.add_column("A", no_wrap=True)
table.add_column("B", no_wrap=True)

for idx, row in df.iterrows():
    a_val = row["A"]
    b_val = row["B"]
    # Style: green background if equal, red if different
    style = "on red" if a_val != b_val else ""
    # if a_val == b_val:
    #     style = "on green"
    # else:
    #     style = "on red"
    table.add_row(
        str(idx),
        repr(a_val),
        repr(b_val),
        style=style
    )

console.print(table)