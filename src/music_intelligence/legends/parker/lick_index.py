"""Parker vocabulary query entry point."""
from .vocabulary import PARKER_LEGEND_ID, VocabularyIndex, VocabularyQuery


class ParkerVocabularyIndex(VocabularyIndex):
    def query_parker(self, **kwargs):
        kwargs.setdefault("legend_id", PARKER_LEGEND_ID)
        return self.query(VocabularyQuery(**kwargs))
