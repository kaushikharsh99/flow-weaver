import os
import json
from sqlalchemy.orm import Session
from app.models import Template

def seed_templates(db: Session):
    """Seed the database with default AI dataset preprocessing templates from the templates directory."""
    print("Seeding default FlowWeaver preprocessing templates...")
    
    # Clear existing templates to remove old/stale hardcoded data
    db.query(Template).delete()
    
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    if os.path.exists(templates_dir):
        count = 0
        for filename in os.listdir(templates_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(templates_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    pipeline_data = {
                        "nodes": data.get("nodes", []),
                        "edges": data.get("edges", [])
                    }
                    
                    t = Template(
                        id=data["id"],
                        name=data["name"],
                        description=data.get("description", ""),
                        pipeline_data=pipeline_data
                    )
                    db.add(t)
                    count += 1
                    print(f"Loaded template: {data['name']} ({data['id']})")
                except Exception as e:
                    print(f"Error loading template {filename}: {e}")
                    
        db.commit()
        print(f"✔ {count} preprocessing templates seeded successfully.")
    else:
        print(f"Warning: templates directory not found at {templates_dir}")
