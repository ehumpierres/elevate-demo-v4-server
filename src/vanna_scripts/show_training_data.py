import pandas as pd
import sys
from src.vanna_scripts.vanna_snowflake import VannaSnowflake
from tabulate import tabulate
from typing import Optional

class TrainingDataViewer:
    def __init__(self):
        """Initialize the TrainingDataViewer."""
        self.training_data = None
        self.vanna_snowflake = VannaSnowflake()
        self.load_training_data()

    def truncate_text(self, text, max_length=100):
        """Truncate text to a maximum length."""
        if pd.isna(text):
            return ""
        return str(text[:max_length]) + "..." if len(str(text)) > max_length else str(text)

    def load_training_data(self) -> None:
        """Load the current training data from Vanna."""
        try:
            self.training_data = self.vanna_snowflake.vanna_ai.get_training_data()
            if not isinstance(self.training_data, pd.DataFrame):
                raise TypeError("Expected DataFrame but got different type from vanna_ai.get_training_data()")
        except Exception as e:
            print(f"Error loading training data: {e}")
            self.training_data = pd.DataFrame()

    def _is_natural_language_question(self, question_series):
        """Helper method to identify natural language questions vs technical descriptions."""
        return (
            (question_series.notna()) & 
            (question_series != '') &
            (question_series.str.match(r'^\s*(?:What|How|Which|Who|Where|When|Why|Can|Could|Would|Should|Do|Does|Did|Is|Are|Was|Were)\b', case=False, na=False))
        )

    def get_stats(self) -> dict:
        """Get statistics about the training data."""
        if self.training_data.empty:
            return {
                "total_entries": 0,
                "ddl_count": 0,
                "documentation_count": 0,
                "sql_count": 0,
                "qa_pairs_count": 0
            }

        # Count by training_data_type
        type_counts = self.training_data['training_data_type'].value_counts().to_dict() if 'training_data_type' in self.training_data.columns else {}
        
        # Distinguish between SQL examples and Q&A pairs based on training approach
        qa_pairs_count = 0
        sql_examples_count = 0
        
        if 'question' in self.training_data.columns and 'content' in self.training_data.columns:
            # Q&A pairs: entries trained with both question and sql parameters
            # These have natural language questions (starting with question words)
            qa_pairs_mask = self._is_natural_language_question(self.training_data['question'])
            qa_pairs_count = qa_pairs_mask.sum()
            
            # SQL examples: entries trained with only sql parameter (from .sql files)
            # These may have technical descriptions but not natural language questions
            sql_mask = (self.training_data['training_data_type'] == 'sql') & ~qa_pairs_mask
            sql_examples_count = sql_mask.sum()
        else:
            # Fallback to original logic if columns are missing
            qa_pairs_count = type_counts.get('question_answer', 0)
            sql_examples_count = type_counts.get('sql', 0)
        
        stats = {
            "total_entries": len(self.training_data),
            "ddl_count": type_counts.get('ddl', 0),
            "documentation_count": type_counts.get('documentation', 0),
            "sql_count": sql_examples_count,
            "qa_pairs_count": qa_pairs_count
        }
        return stats

    def display_stats(self) -> None:
        """Display statistics about the training data."""
        stats = self.get_stats()
        print("\n=== Training Data Statistics ===")
        print(f"Total entries: {stats['total_entries']}")
        print(f"DDL statements: {stats['ddl_count']}")
        print(f"Documentation entries: {stats['documentation_count']}")
        print(f"SQL examples: {stats['sql_count']}")
        print(f"Question-SQL pairs: {stats['qa_pairs_count']}")
        
        # Print column names
        if not self.training_data.empty:
            print("\n=== Available Columns ===")
            print(list(self.training_data.columns))

    def display_data(self, data_type: Optional[str] = None, max_rows: int = 5) -> None:
        """
        Display the training data in a formatted table.
        
        Args:
            data_type (str, optional): Filter by type ('ddl', 'documentation', 'sql', or 'qa'). 
                                     If None, show all types.
            max_rows (int): Maximum number of rows to display per type.
        """
        if self.training_data.empty:
            print("\nNo training data available.")
            return

        # Check if required columns exist
        required_cols = ['training_data_type', 'content', 'question']
        missing_cols = [col for col in required_cols if col not in self.training_data.columns]
        if missing_cols:
            print(f"\nWarning: Missing columns: {missing_cols}")
            return

        if data_type:
            if data_type == 'ddl':
                subset = self.training_data[self.training_data['training_data_type'] == 'ddl']
                self._display_section('DDL Statements', subset[['content']], max_rows)
            elif data_type == 'documentation':
                subset = self.training_data[self.training_data['training_data_type'] == 'documentation']
                self._display_section('Documentation', subset[['content']], max_rows)
            elif data_type == 'sql':
                # Show SQL examples (from .sql files) - entries without natural language questions
                if 'question' in self.training_data.columns:
                    qa_pairs_mask = self._is_natural_language_question(self.training_data['question'])
                    subset = self.training_data[(self.training_data['training_data_type'] == 'sql') & ~qa_pairs_mask]
                else:
                    subset = self.training_data[self.training_data['training_data_type'] == 'sql']
                self._display_section('SQL Examples', subset[['content']], max_rows)
            elif data_type == 'qa':
                # Show Q&A pairs (from JSON files) - entries with natural language questions
                if 'question' in self.training_data.columns and 'content' in self.training_data.columns:
                    qa_pairs_mask = self._is_natural_language_question(self.training_data['question'])
                    subset = self.training_data[qa_pairs_mask]
                    self._display_section('Question-SQL Pairs', 
                                        subset[['question', 'content']], max_rows)
                else:
                    subset = self.training_data[self.training_data['training_data_type'] == 'question_answer']
                    self._display_section('Question-SQL Pairs', 
                                        subset[['question', 'content']], max_rows)
            else:
                print(f"\nNo data available for type: {data_type}")
        else:
            # Display all types
            print("\n=== Current Training Data ===")
            for dtype in ['ddl', 'documentation', 'sql', 'qa']:
                self.display_data(dtype, max_rows)

    def _display_section(self, title: str, data: pd.DataFrame, max_rows: int) -> None:
        """Helper method to display a section of the training data."""
        if not data.empty:
            print(f"\n--- {title} ---")
            # Truncate and format the data
            formatted_data = data.head(max_rows).copy()
            for col in formatted_data.columns:
                formatted_data[col] = formatted_data[col].map(
                    lambda x: self.truncate_text(x) if pd.notna(x) else '')
            print(tabulate(formatted_data, headers='keys', 
                         tablefmt='grid', showindex=False))
            if len(data) > max_rows:
                print(f"... and {len(data) - max_rows} more entries")

def main():
    viewer = TrainingDataViewer()
    
    # Display statistics
    viewer.display_stats()
    
    # Display all training data
    viewer.display_data()
    
    print("\nTo view specific types, run with arguments:")
    print("python show_training_data.py [data_type] [max_rows]")
    print("data_type options: ddl, documentation, sql, qa")

if __name__ == "__main__":
    viewer = TrainingDataViewer()
    
    if len(sys.argv) > 1:
        data_type = sys.argv[1].lower()
        max_rows = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        if data_type in ['ddl', 'documentation', 'sql', 'qa']:
            viewer.display_stats()
            viewer.display_data(data_type, max_rows)
        else:
            print(f"Invalid data type: {data_type}")
            print("Available types: ddl, documentation, sql, qa")
    else:
        main() 