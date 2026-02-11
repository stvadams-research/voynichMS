from typing import List, Optional
import matplotlib.pyplot as plt
import numpy as np
from sqlalchemy import func
import logging

from visualization.base import BaseVisualizer
from visualization.core.themes import apply_voynich_theme, get_color_palette
from foundation.storage.metadata import (
    PageRecord, 
    TranscriptionLineRecord, 
    TranscriptionTokenRecord
)

logger = logging.getLogger(__name__)

class FoundationVisualizer(BaseVisualizer):
    """
    Visualizers for Layer 1 (Foundation).
    Focuses on token distributions and basic manuscript structure.
    """

    @property
    def phase_name(self) -> str:
        return "foundation"

    def plot_token_frequency(self, dataset_id: str, top_n: int = 50) -> Optional[str]:
        """
        Generate a Zipfian distribution plot for tokens in a dataset.
        """
        apply_voynich_theme()
        session = self.store.Session()
        try:
            # Query token frequencies
            query = (
                session.query(
                    TranscriptionTokenRecord.content,
                    func.count(TranscriptionTokenRecord.id).label('count')
                )
                .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
                .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
                .filter(PageRecord.dataset_id == dataset_id)
                .group_by(TranscriptionTokenRecord.content)
                .order_by(func.count(TranscriptionTokenRecord.id).desc())
            )
            
            results = query.all()
            if not results:
                logger.warning(f"No tokens found for dataset {dataset_id}")
                return None
            
            tokens = [r[0] for r in results[:top_n]]
            counts = [r[1] for r in results[:top_n]]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.bar(tokens, counts)
            ax.set_title(f"Token Frequency Distribution (Top {top_n}) - {dataset_id}")
            ax.set_xlabel("Token")
            ax.set_ylabel("Frequency")
            plt.xticks(rotation=45, ha='right')
            
            # Add log-log inset for Zipfian check
            all_counts = [r[1] for r in results]
            ranks = np.arange(1, len(all_counts) + 1)
            
            ax_inset = fig.add_axes([0.65, 0.65, 0.2, 0.2])
            ax_inset.loglog(ranks, all_counts)
            ax_inset.set_title("Zipf Law (Log-Log)")
            ax_inset.set_xlabel("Rank")
            ax_inset.set_ylabel("Freq")
            
            filename = f"token_frequency_{dataset_id}.png"
            output_path = self._save_figure(fig, filename, metadata={
                "dataset_id": dataset_id,
                "top_n": top_n,
                "total_unique_tokens": len(results),
                "total_tokens": sum(all_counts)
            })
            
            plt.close(fig)
            return str(output_path)
            
        finally:
            session.close()

    def plot_repetition_rate(self, dataset_id: str) -> Optional[str]:
        """
        Generate a histogram of repetition rates across pages in a dataset.
        """
        apply_voynich_theme()
        session = self.store.Session()
        try:
            # We want page-level repetition rates
            # Note: This logic mimics Foundation metrics but at page granularity
            pages = session.query(PageRecord).filter_by(dataset_id=dataset_id).all()
            
            page_rates = []
            for page in pages:
                tokens = (
                    session.query(TranscriptionTokenRecord.content)
                    .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
                    .filter(TranscriptionLineRecord.page_id == page.id)
                    .all()
                )
                
                if not tokens:
                    continue
                
                token_contents = [t[0] for t in tokens]
                total = len(token_contents)
                from collections import Counter
                counts = Counter(token_contents)
                repeated = sum(count for count in counts.values() if count > 1)
                page_rates.append(repeated / total if total > 0 else 0.0)
            
            if not page_rates:
                logger.warning(f"No repetition rate data for dataset {dataset_id}")
                return None
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(page_rates, bins=20, alpha=0.7, color=get_color_palette()[0])
            ax.axvline(np.mean(page_rates), color=get_color_palette()[1], linestyle='dashed', linewidth=2, label=f'Mean: {np.mean(page_rates):.3f}')
            
            ax.set_title(f"Page-level Repetition Rate Distribution - {dataset_id}")
            ax.set_xlabel("Repetition Rate")
            ax.set_ylabel("Page Count")
            ax.legend()
            
            filename = f"repetition_rate_dist_{dataset_id}.png"
            output_path = self._save_figure(fig, filename, metadata={
                "dataset_id": dataset_id,
                "page_count": len(page_rates),
                "mean_rate": float(np.mean(page_rates)),
                "std_rate": float(np.std(page_rates))
            })
            
            plt.close(fig)
            return str(output_path)
            
        finally:
            session.close()
