import re

def clean_token(t):
    """Removes transcription metadata and punctuation from a token."""
    t = re.sub(r'<!.*?>', '', t)
    t = re.sub(r'<.*?>', '', t)
    t = re.sub(r'[,\.;]', '', t)
    return t.strip()

class ErgonomicCostAnalyzer:
    """Calculates physical effort scores for tokens based on stroke complexity."""
    
    def __init__(self, token_features):
        """
        Args:
            token_features (dict): Mapping from token to feature dictionary (Phase 11 format).
        """
        self.token_features = token_features
        self.word_to_strokes = {}
        for raw_t, feats in token_features.items():
            clean = clean_token(raw_t)
            if not clean:
                continue
            # mean_profile index 5 is 'stroke_count'
            profile = feats.get("mean_profile", [])
            if len(profile) > 5:
                self.word_to_strokes[clean] = profile[5]

    def calculate_cost(self, word):
        """
        Calculates effort score for a single word.
        
        Total Effort = Strokes + (2.0 * gallows) + (1.5 * descenders)
        """
        if word in self.word_to_strokes:
            base_cost = self.word_to_strokes[word]
            # Index 0: gallows, Index 3: descender
            profile = self.token_features.get(word, {}).get("mean_profile", [0]*7)
            gallows = profile[0] if len(profile) > 0 else 0
            descenders = profile[3] if len(profile) > 3 else 0
            return float(base_cost + (2.0 * gallows) + (1.5 * descenders))
        else:
            # Estimation for missing tokens: length * avg stroke count (1.5)
            return float(len(word) * 1.5)

    def batch_process(self, words):
        """Calculates costs for a list of words."""
        costs = {}
        missing_count = 0
        for word in words:
            if word not in self.word_to_strokes:
                missing_count += 1
            costs[word] = self.calculate_cost(word)
        return costs, missing_count
