from hyperon import MeTTa, S, E, ValueAtom

class FinancialRAG:
    """
    Provides an interface to query and UPDATE our MeTTa knowledge graph
    for financial information like optimal paths and exchange rates.
    """
    def __init__(self, metta_instance: MeTTa):
        self.metta = metta_instance

    def update_rate(self, from_currency: str, to_currency: str, rate: float):
        """Adds or updates a rate atom in the knowledge graph."""
        self.metta.space().add_atom(E(S("rate"), S(from_currency), S(to_currency), ValueAtom(rate)))
        print(f"[KG LOG] Updated rate for {from_currency}->{to_currency} to {rate}")

    def find_best_path(self, from_currency: str, to_currency: str) -> str | None:
        """
        Queries the knowledge graph to find the most cost-effective intermediate
        currency ('via') for a conversion.
        """
        try:
            query_str = f'!(match &self (path {from_currency} {to_currency} $via $cost) ($via $cost))'
            results = self.metta.run(query_str)

            if not results or not results[0]:
                return None
            
            best_item = min(results[0], key=lambda item: float(str(item.get_children()[1])))
            best_path_via = str(best_item.get_children()[0])
            return best_path_via
        except Exception as e:
            print(f"[ERROR in RAG] Could not find best path: {e}")
            return None

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float | None:
        """Queries the knowledge graph for a specific exchange rate."""
        try:
            query_str = f'!(match &self (rate {from_currency} {to_currency} $rate) $rate)'
            result = self.metta.run(query_str)
            if result and result[0]:
                return float(str(result[0][0]))
            return None
        except Exception as e:
            print(f"[ERROR in RAG] Could not query exchange rate: {e}")
            return None

