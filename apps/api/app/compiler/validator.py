from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass, field


@dataclass
class ValidationIssue:
    node_id: Optional[str]
    level: str  # "error" | "warning"
    message: str


@dataclass
class ValidationResult:
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "error"]

    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "warning"]


class PipelineValidator:
    """Validates visual pipeline DAG structure prior to code compilation."""

    @classmethod
    def validate(cls, pipeline_dict: Dict[str, Any]) -> ValidationResult:
        issues: List[ValidationIssue] = []

        nodes = pipeline_dict.get("nodes", [])
        edges = pipeline_dict.get("edges", [])

        if not nodes:
            issues.append(ValidationIssue(node_id=None, level="error", message="Pipeline contains no nodes."))
            return ValidationResult(valid=False, issues=issues)

        # 1. Check duplicate node IDs
        seen_ids: Set[str] = set()
        for node in nodes:
            n_id = node.get("id")
            if not n_id:
                issues.append(ValidationIssue(node_id=None, level="error", message="Found node missing 'id' field."))
            elif n_id in seen_ids:
                issues.append(ValidationIssue(node_id=n_id, level="error", message=f"Duplicate node ID found: '{n_id}'."))
            else:
                seen_ids.add(n_id)

        # 2. Build adjacency list and check cycle (DAG check)
        adj: Dict[str, List[str]] = {n.get("id"): [] for n in nodes if n.get("id")}
        in_degree: Dict[str, int] = {n.get("id"): 0 for n in nodes if n.get("id")}

        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src in adj and tgt in in_degree:
                adj[src].append(tgt)
                in_degree[tgt] += 1
            else:
                issues.append(ValidationIssue(
                    node_id=src,
                    level="warning",
                    message=f"Edge refers to non-existent node: source='{src}', target='{tgt}'."
                ))

        # Kahn's algorithm for cycle detection
        queue = [n_id for n_id, deg in in_degree.items() if deg == 0]
        visited_count = 0

        while queue:
            curr = queue.pop(0)
            visited_count += 1
            for neighbor in adj.get(curr, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count < len(in_degree):
            issues.append(ValidationIssue(node_id=None, level="error", message="Cycle detected in pipeline graph. Pipelines must be directed acyclic graphs (DAG)."))

        # 3. Check for disconnected intermediate nodes
        connected_nodes = set()
        for edge in edges:
            if edge.get("source"):
                connected_nodes.add(edge.get("source"))
            if edge.get("target"):
                connected_nodes.add(edge.get("target"))

        if len(nodes) > 1:
            for node in nodes:
                n_id = node.get("id")
                if n_id and n_id not in connected_nodes:
                    issues.append(ValidationIssue(node_id=n_id, level="warning", message=f"Node '{n_id}' is disconnected from the rest of the pipeline graph."))

        has_errors = any(i.level == "error" for i in issues)
        return ValidationResult(valid=not has_errors, issues=issues)
