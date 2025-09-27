from hyperon import MeTTa, E, S, ValueAtom

def initialize_financial_knowledge_graph(metta: MeTTa):
    """
    Populates the MeTTa space with the structural knowledge of valid
    conversion paths and their associated costs.
    Rates are no longer stored here; they will be added dynamically.
    """
    # --- Define valid conversion paths and their costs ---
    # (path <from> <to> <via> <cost>)
    # Cost is a relative metric; lower is better. It represents fees, slippage etc.
    metta.space().add_atom(E(S("path"), S("INR"), S("USD"), S("ETH"), ValueAtom(0.001)))
    metta.space().add_atom(E(S("path"), S("INR"), S("USD"), S("MATIC"), ValueAtom(0.0008))) # Lower cost path