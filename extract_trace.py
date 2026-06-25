import os
import json
from langfuse import Langfuse

# Explicitly pointing to your self-hosted instance
langfuse = Langfuse(
    public_key="your-public-key",
    secret_key="your-secret-key",
    host="http://localhost:3000"  # Change to your self-hosted URL
)

def extract_mcp_trajectory(trace_id: str, output_file: str = "mock_trajectory.json"):
    print(f"Fetching trace {trace_id} from self-hosted Langfuse ({langfuse.base_url})...")
    
    # Rest of the code remains exactly the same as before
    observations = langfuse.get_observations(trace_id=trace_id)
    
    trajectory = {}
    for obs in observations.data:
        if obs.type == "TOOL":
            tool_name = obs.name
            if tool_name not in trajectory:
                trajectory[tool_name] = []
                
            trajectory[tool_name].append({
                "expected_input": obs.input,
                "mocked_output": obs.output
            })
            
    with open(output_file, 'w') as f:
        json.dump(trajectory, f, indent=2)
        
    print(f"Successfully extracted tool calls to {output_file}")

if __name__ == "__main__":
    extract_mcp_trajectory("your-langfuse-trace-id")
