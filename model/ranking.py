
from config import Config

class Ranking:
    """ランキングシステム（メモリ上のみ）"""
    def __init__(self):
        # 初期ランキング（ダミーデータ）
        self.rankings = [
            {"name": "SSS", "score": 1000, "lines": 50},
            {"name": "CPU", "score": 900, "lines": 40},
            {"name": "BBB", "score": 800, "lines": 30},
            {"name": "CCC", "score": 700, "lines": 20},
            {"name": "DDD", "score": 600, "lines": 10},
            {"name": "EEE", "score": 500, "lines": 9},
            {"name": "FFF", "score": 450, "lines": 8},
            {"name": "GGG", "score": 400, "lines": 7},
            {"name": "HHH", "score": 350, "lines": 6},
            {"name": "III", "score": 300, "lines": 5},

        ]
    
    def check_ranking(self, score):
        """スコアがランクインするか確認"""
        if len(self.rankings) < Config.RANKING_MAX:
            return True
        return score > self.rankings[-1]['score']
    
    def get_rank(self, score):
        """スコアが何位になるか取得（1-based）"""
        for i, entry in enumerate(self.rankings):
            if score > entry['score']:
                return i + 1
        if len(self.rankings) < Config.RANKING_MAX:
            return len(self.rankings) + 1
        return None
    
    def add_entry(self, name, score, lines):
        """ランキングにエントリーを追加"""
        entry = {
            "name": name.upper()[:3],  # 3文字まで、大文字に変換
            "score": score,
            "lines": lines
        }
        
        # 適切な位置に挿入
        self.rankings.append(entry)
        self.rankings.sort(key=lambda x: x['score'], reverse=True)
        
        # 10位まで保持
        self.rankings = self.rankings[:Config.RANKING_MAX]
    
    def get_rankings(self):
        """ランキング一覧を取得"""
        return self.rankings