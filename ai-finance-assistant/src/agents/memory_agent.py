from typing import Dict, Any, List

def update_profile(profile: Dict[str, Any], user_message: str) -> Dict[str, Any]:
    # simple heuristic extraction
    t = user_message.lower()
    if "beginner" in t:
        profile["experience"] = "beginner"
    if "intermediate" in t:
        profile["experience"] = "intermediate"
    if "aggressive" in t:
        profile["risk_tolerance"] = "aggressive"
    if "conservative" in t:
        profile["risk_tolerance"] = "conservative"
    if "moderate" in t:
        profile["risk_tolerance"] = "moderate"
    return profile

def append_memory(memory: List[Dict[str, str]], role: str, content: str) -> List[Dict[str, str]]:
    memory = memory or []
    memory.append({"role": role, "content": content})
    # keep last 20
    return memory[-20:]