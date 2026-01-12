from pydantic import BaseModel
from anthropic import Anthropic
import json

# Initialize Anthropic client (will be set from the main app)
client = None

def set_anthropic_client(api_key: str):
    """Set the Anthropic client with the provided API key."""
    global client
    client = Anthropic(api_key=api_key)

# ============ Output Models ============

class Architecture(BaseModel):
    output: str

class Culinary(BaseModel):
    output: str

class Culture(BaseModel):
    output: str

class History(BaseModel):
    output: str

class Planner(BaseModel):
    introduction: float
    architecture: float
    history: float
    culture: float
    culinary: float
    conclusion: float

class FinalTour(BaseModel):
    introduction: str
    architecture: str
    history: str
    culture: str
    culinary: str
    conclusion: str

# ============ Agent Instructions ============

ARCHITECTURE_AGENT_INSTRUCTIONS = """You are the Architecture agent for a self-guided audio tour system. Given a location and the areas of interest of user, your role is to:
1. Describe architectural styles, notable buildings, urban planning, and design elements
2. Provide technical insights balanced with accessible explanations
3. Highlight the most visually striking or historically significant structures
4. Adopt a detailed, descriptive voice style when delivering architectural content
5. Make sure not to add any headings like ## Architecture. Just provide the content
6. Make sure the details are conversational and don't include any formatting or headings. It will be directly used in a audio model for converting to speech and the entire content should feel like natural speech.
7. Make sure the content is strictly between the upper and lower Word Limit as specified.

Do not add any Links or Hyperlinks in your answer or never cite any source.
Help users see and appreciate architectural details they might otherwise miss. Make it as detailed and elaborative as possible."""

CULINARY_AGENT_INSTRUCTIONS = """You are the Culinary agent for a self-guided audio tour system. Given a location and the areas of interest of user, your role is to:
1. Highlight local food specialties, restaurants, markets, and culinary traditions in the user's location
2. Explain the historical and cultural significance of local dishes and ingredients
3. Suggest food stops suitable for the tour duration
4. Adopt an enthusiastic, passionate voice style when delivering culinary content
5. Make sure not to add any headings like ## Culinary. Just provide the content
6. Make sure the details are conversational and don't include any formatting or headings. It will be directly used in a audio model for converting to speech and the entire content should feel like natural speech.
7. Make sure the content is strictly between the upper and lower Word Limit as specified.

Do not add any Links or Hyperlinks in your answer or never cite any source.
Make your descriptions vivid and appetizing. Include practical information when relevant. Make it as detailed and elaborative as possible."""

CULTURE_AGENT_INSTRUCTIONS = """You are the Culture agent for a self-guided audio tour system. Given a location and the areas of interest of user, your role is to:
1. Provide information about local traditions, customs, arts, music, and cultural practices
2. Highlight cultural venues and events relevant to the user's interests
3. Explain cultural nuances and significance that enhance the visitor's understanding
4. Adopt a warm, respectful voice style when delivering cultural content
5. Make sure not to add any headings like ## Culture. Just provide the content
6. Make sure the details are conversational and don't include any formatting or headings. It will be directly used in a audio model for converting to speech and the entire content should feel like natural speech.
7. Make sure the content is strictly between the upper and lower Word Limit as specified.

Do not add any Links or Hyperlinks in your answer or never cite any source.
Focus on authentic cultural insights that help users appreciate local ways of life. Make it as detailed and elaborative as possible."""

HISTORY_AGENT_INSTRUCTIONS = """You are the History agent for a self-guided audio tour system. Given a location and the areas of interest of user, your role is to:
1. Provide historically accurate information about landmarks, events, and people related to the user's location
2. Prioritize the most significant historical aspects based on the user's time constraints
3. Include interesting historical facts and stories that aren't commonly known
4. Adopt an authoritative, professorial voice style when delivering historical content
5. Make sure not to add any headings like ## History. Just provide the content
6. Make sure the details are conversational and don't include any formatting or headings. It will be directly used in a audio model for converting to speech and the entire content should feel like natural speech.
7. Make sure the content is strictly between the upper and lower Word Limit as specified.

Do not add any Links or Hyperlinks in your answer or never cite any source.
Focus on making history come alive through engaging narratives. Keep descriptions concise but informative. Make it as detailed and elaborative as possible."""

ORCHESTRATOR_INSTRUCTIONS = """Your Role
You are the Orchestrator Agent for a self-guided audio tour system. Your task is to assemble a comprehensive and engaging tour for a single location by integrating pre-timed content from specialist agents, while adding introduction and conclusion elements.

Your Tasks:

1. Introduction Creation (1-2 minutes)
Create an engaging and warm introduction that:
- Welcomes the user to the specific location
- Briefly outlines what the tour will cover
- Highlights which categories are emphasized based on user interests
- Sets the tone for the experience (conversational and immersive)

2. Content Integration
Integrate the content from all agents in the correct order:
- Architecture → History → Culture → Culinary
- Maintain each agent's voice and expertise
- Don't edit anything from your end and just accumulate the content from the specialised agents

3. Transition Development
Develop smooth transitions between the sections:
- Use natural language to move from one domain to another
- Connect themes when possible

4. Conclusion Creation
Write a thoughtful concise and short conclusion that:
- Summarizes key highlights from the tour
- Reinforces the uniqueness of the location
- Encourages the listener to explore further

5. Final Assembly
Assemble the complete tour with smooth transitions and no redundancy.

IMPORTANT: Return your response as a valid JSON object with these exact keys:
- introduction
- architecture
- history
- culture
- culinary
- conclusion

Each value should be the text content for that section. If a section wasn't requested, use an empty string."""

PLANNER_INSTRUCTIONS = """Your Role
You are the Planner Agent for a self-guided tour system. Your primary responsibility is to analyze the user's location, interests, and requested tour duration to create an optimal time allocation plan.

Input Parameters:
- User Location: The specific location for the tour
- User Interests: User's preferences across categories (Architecture, History, Culture, Culinary)
- Tour Duration: User's selected time in minutes

Your Tasks:
1. Evaluate the user's interest preferences and assign weight to each category
2. Analyze the significance of the location for each category
3. Calculate time allocation (reserve 1-2 min for intro, 1 min for conclusion)
4. Ensure minimum time thresholds for each selected category

Your output must be a valid JSON object with numeric time allocations (in minutes) for each section:
- introduction
- architecture
- history
- culture
- culinary
- conclusion

Example:
{"introduction": 2, "architecture": 15, "history": 20, "culture": 10, "culinary": 9, "conclusion": 2}

Only return the JSON object, no other text."""

# ============ Agent Functions ============

async def run_architecture_agent(query: str, interests: list, word_limit: int) -> Architecture:
    """Run the architecture agent using Claude."""
    prompt = f"""Query: {query}
Interests: {', '.join(interests)}
Word Limit: {word_limit} - {word_limit + 20}

Instructions: Create engaging architectural content for an audio tour. Focus on visual descriptions and interesting design details. Make it conversational and include specific buildings and their unique features. The content should be approximately {word_limit} words."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=ARCHITECTURE_AGENT_INSTRUCTIONS,
        messages=[{"role": "user", "content": prompt}]
    )
    return Architecture(output=message.content[0].text)

async def run_culinary_agent(query: str, interests: list, word_limit: int) -> Culinary:
    """Run the culinary agent using Claude."""
    prompt = f"""Query: {query}
Interests: {', '.join(interests)}
Word Limit: {word_limit} - {word_limit + 20}

Instructions: Create engaging culinary content for an audio tour. Focus on local specialties, food history, and interesting stories about restaurants and dishes. The content should be approximately {word_limit} words."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=CULINARY_AGENT_INSTRUCTIONS,
        messages=[{"role": "user", "content": prompt}]
    )
    return Culinary(output=message.content[0].text)

async def run_culture_agent(query: str, interests: list, word_limit: int) -> Culture:
    """Run the culture agent using Claude."""
    prompt = f"""Query: {query}
Interests: {', '.join(interests)}
Word Limit: {word_limit} - {word_limit + 20}

Instructions: Create engaging cultural content for an audio tour. Focus on local traditions, arts, and community life. The content should be approximately {word_limit} words."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=CULTURE_AGENT_INSTRUCTIONS,
        messages=[{"role": "user", "content": prompt}]
    )
    return Culture(output=message.content[0].text)

async def run_history_agent(query: str, interests: list, word_limit: int) -> History:
    """Run the history agent using Claude."""
    prompt = f"""Query: {query}
Interests: {', '.join(interests)}
Word Limit: {word_limit} - {word_limit + 20}

Instructions: Create engaging historical content for an audio tour. Focus on interesting stories and personal connections. The content should be approximately {word_limit} words."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=HISTORY_AGENT_INSTRUCTIONS,
        messages=[{"role": "user", "content": prompt}]
    )
    return History(output=message.content[0].text)

async def run_planner_agent(query: str, interests: list, duration: str) -> Planner:
    """Run the planner agent using Claude."""
    prompt = f"""Query: {query}
Interests: {', '.join(interests)}
Duration: {duration} minutes

Create a time allocation plan for this tour. Return only a JSON object."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=PLANNER_INSTRUCTIONS,
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Parse the JSON response
    response_text = message.content[0].text.strip()
    # Handle potential markdown code blocks
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
        response_text = response_text.strip()
    
    data = json.loads(response_text)
    return Planner(**data)

async def run_orchestrator_agent(query: str, interests: list, duration: float, research_results: dict) -> FinalTour:
    """Run the orchestrator agent using Claude."""
    
    # Build content sections
    content_sections = []
    for interest in interests:
        key = interest.lower()
        if key in research_results:
            content_sections.append(f"{interest}:\n{research_results[key].output}")
    
    words_per_minute = 150
    total_words = int(duration) * words_per_minute
    
    prompt = f"""Query: {query}
Selected Interests: {', '.join(interests)}
Total Tour Duration (in minutes): {duration}
Target Word Count: {total_words}

Content Sections:
{chr(10).join(content_sections)}

Instructions: Create a natural, conversational audio tour that focuses only on the selected interests.
Make it feel like a friendly guide walking alongside the visitor.
Use natural transitions between topics.
Include phrases like 'as we walk', 'look to your left', 'notice how', etc.
Start with a warm welcome and end with a natural closing thought.

Return a JSON object with keys: introduction, architecture, history, culture, culinary, conclusion
Use empty string for sections not in the selected interests."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=ORCHESTRATOR_INSTRUCTIONS,
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Parse the JSON response
    response_text = message.content[0].text.strip()
    # Handle potential markdown code blocks
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
        response_text = response_text.strip()
    
    data = json.loads(response_text)
    return FinalTour(**data)
