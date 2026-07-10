from livekit.agents import AgentSession

print([x for x in dir(AgentSession) if "event" in x.lower()])

print("--------------------------------")

print([x for x in dir(AgentSession) if "on" in x.lower()])