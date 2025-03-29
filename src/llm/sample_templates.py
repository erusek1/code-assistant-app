"""
Sample Templates - Provides sample templates for various analysis types
"""
import os
from pathlib import Path
from typing import Dict, Optional

class SampleTemplates:
    """
    Provides sample templates for various types of code analysis to ensure 
    consistent formatting and structure in analysis results.
    """
    
    def __init__(self, samples_dir: Optional[Path] = None):
        """
        Initialize the sample templates handler.
        
        Args:
            samples_dir: Directory containing sample template files
        """
        # Use the default samples directory if none is provided
        if samples_dir is None:
            base_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            samples_dir = base_dir / "data" / "samples"
        
        self.samples_dir = samples_dir
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all available templates from the samples directory."""
        if not self.samples_dir.exists():
            print(f"Warning: Samples directory {self.samples_dir} does not exist.")
            return
        
        # Load each sample file
        for template_file in self.samples_dir.glob("*_sample.md"):
            template_name = template_file.stem.replace("_sample", "")
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    self.templates[template_name] = f.read()
                print(f"Loaded template: {template_name}")
            except Exception as e:
                print(f"Error loading template {template_file}: {e}")
    
    def get_template(self, analysis_type: str) -> Optional[str]:
        """
        Get a sample template for the specified analysis type.
        
        Args:
            analysis_type: Type of analysis (standard, security, performance, project)
            
        Returns:
            Template content if available, None otherwise
        """
        return self.templates.get(analysis_type.lower())
    
    def get_all_templates(self) -> Dict[str, str]:
        """
        Get all available templates.
        
        Returns:
            Dictionary of template names to content
        """
        return self.templates
    
    def get_template_names(self) -> list:
        """
        Get the names of all available templates.
        
        Returns:
            List of template names
        """
        return list(self.templates.keys())
    
    def get_template_prompt(self, analysis_type: str) -> str:
        """
        Get a prompt that incorporates the sample template for the LLM.
        
        Args:
            analysis_type: Type of analysis (standard, security, performance, project)
            
        Returns:
            Prompt text with embedded sample template
        """
        template = self.get_template(analysis_type)
        if not template:
            return ""
        
        prompt = f"""
Please follow this format for your {analysis_type} analysis:

```markdown
{template}
```

Use this as a template for your analysis, adapting it to the specific code being analyzed. 
Keep the same structured format with appropriate sections and formatting. 
Be specific about line numbers, include code snippets, and provide concrete recommendations.
"""
        return prompt
