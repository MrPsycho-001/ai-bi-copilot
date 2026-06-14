import pandas as pd
import pathlib

class LocalDataAnalyzer:
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        ext = pathlib.Path(dataset_path).suffix.lower()
        
        try:
            if ext == '.csv':
                self.df = pd.read_csv(dataset_path)
            elif ext in ['.xlsx', '.xls']:
                try:
                    self.df = pd.read_excel(dataset_path)
                except Exception:
                    # Fallback to CSV parser if Excel engine rejects the layout structure
                    self.df = pd.read_csv(dataset_path)
            elif ext == '.json':
                self.df = pd.read_json(dataset_path)
            else:
                raise ValueError(f"Unsupported data format: {ext}")
        except Exception as e:
            raise RuntimeError(f"Engine parsing failure: {str(e)}")

    def generate_summary_profile(self) -> dict:
        profile = {}
        profile['standard_metrics'] = self.df.describe().to_dict()
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        categorical_cols = self.df.select_dtypes(include=['object', 'string']).columns
        
        profile['top_5_rankings'] = {}
        profile['bottom_5_rankings'] = {}
        profile['categorical_counts'] = {}
        
        for col in numeric_cols:
            profile['top_5_rankings'][col] = self.df.nlargest(5, col).fillna("N/A").to_dict(orient='records')
            profile['bottom_5_rankings'][col] = self.df.nsmallest(5, col).fillna("N/A").to_dict(orient='records')
            
        for col in categorical_cols:
            profile['categorical_counts'][col] = self.df[col].value_counts().head(5).to_dict()
            
        return profile
