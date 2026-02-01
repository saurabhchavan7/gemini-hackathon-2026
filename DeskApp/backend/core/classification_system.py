"""
LifeOS - Universal Classification System
The comprehensive taxonomy for ALL human digital life
"""

# ============================================
# LAYER 1: LIFE DOMAINS (12 Universal Buckets)
# ============================================

LIFE_DOMAINS = {
    "work_career": {
        "name": "Work & Career",
        "description": "Earning, profession, growth",
        "examples": [
            "Job postings", "Office emails", "Slack messages", "Meeting screens",
            "Jira tickets", "Code errors", "Interview prep", "Resume feedback",
            "HR mails", "Freelance invoices", "Performance reviews", "Salary negotiations"
        ]
    },
    "education_learning": {
        "name": "Education & Learning",
        "description": "Formal or informal learning",
        "examples": [
            "Course pages", "YouTube tutorials", "Notes", "Research papers",
            "Exam schedules", "Assignment PDFs", "Online classes", "Certifications",
            "Study materials", "Academic portals", "Training programs"
        ]
    },
    "money_finance": {
        "name": "Money & Finance",
        "description": "Money movement, planning, tracking",
        "examples": [
            "Bills", "Salary slips", "Bank statements", "Credit card dues",
            "Subscriptions", "Insurance", "Taxes", "Investments", "Receipts",
            "Loan statements", "Budget sheets", "Expense tracking"
        ]
    },
    "home_daily_life": {
        "name": "Home & Daily Life",
        "description": "Running daily life",
        "examples": [
            "Rent agreements", "Utility bills", "Groceries", "Repairs",
            "House chores", "Furniture", "Internet plans", "Home maintenance",
            "Appliance manuals", "Service appointments", "Household shopping"
        ]
    },
    "health_wellbeing": {
        "name": "Health & Well-being",
        "description": "Physical and mental health",
        "examples": [
            "Doctor appointments", "Prescriptions", "Lab reports", "Fitness plans",
            "Diet charts", "Therapy notes", "Medical records", "Vaccination cards",
            "Gym memberships", "Wellness apps", "Health insurance"
        ]
    },
    "family_relationships": {
        "name": "Family & Relationships",
        "description": "People you care about",
        "examples": [
            "Family events", "Kids' school", "Parent medical", "Anniversaries",
            "Birthdays", "Relationship chats", "Family planning", "School circulars",
            "Childcare", "Elder care", "Family gatherings"
        ]
    },
    "travel_movement": {
        "name": "Travel & Movement",
        "description": "Movement across places",
        "examples": [
            "Flights", "Trains", "Hotels", "Maps", "Visas", "Itineraries",
            "Boarding passes", "Rental cars", "Travel insurance", "Luggage tracking",
            "Destination research", "Bookings", "Travel guides"
        ]
    },
    "shopping_consumption": {
        "name": "Shopping & Consumption",
        "description": "Buying decisions",
        "examples": [
            "Products", "Offers", "Price comparisons", "Reviews", "Wishlists",
            "Cart screens", "Order tracking", "Return policies", "Coupons",
            "Deal alerts", "Product comparisons"
        ]
    },
    "entertainment_leisure": {
        "name": "Entertainment & Leisure",
        "description": "Fun, enjoyment, rest",
        "examples": [
            "Movies", "Shows", "Music", "Events", "Games", "Hobbies",
            "Concerts", "Sports", "Books", "Podcasts", "Streaming services",
            "Event tickets", "Recreation activities"
        ]
    },
    "social_community": {
        "name": "Social & Community",
        "description": "Public and social interactions",
        "examples": [
            "Social media posts", "Comments", "Groups", "News", "Announcements",
            "Forums", "Online communities", "Public discussions", "Trends",
            "Civic engagement", "Volunteering"
        ]
    },
    "admin_documents": {
        "name": "Admin & Documents",
        "description": "Official, bureaucratic, identity",
        "examples": [
            "Government portals", "IDs", "Applications", "Legal docs", "Forms",
            "Passport", "SSN/Aadhaar", "Licenses", "Permits", "Contracts",
            "Official certificates", "Registration documents"
        ]
    },
    "ideas_thoughts": {
        "name": "Ideas & Personal Thoughts",
        "description": "Brain dump, personal notes",
        "examples": [
            "Ideas", "Thoughts", "Plans", "Notes", "Inspirations",
            "Brainstorming", "Personal reflections", "Goals", "Dreams",
            "Creative writing", "Journal entries"
        ]
    }
}

# ============================================
# LAYER 2: CONTEXT TYPES (What Kind of Thing)
# ============================================

CONTEXT_TYPES = [
    "email",
    "chat_message",
    "document_pdf",
    "web_page",
    "app_screen",
    "form",
    "image_photo",
    "video",
    "spreadsheet",
    "notification",
    "receipt_invoice",
    "calendar_item",
    "social_media_post",
    "code_terminal",
    "presentation",
    "dashboard",
    "settings_screen",
    "map_navigation",
    "list_checklist"
]

# ============================================
# LAYER 3: INTENTS (What to Do)
# ============================================

INTENTS = {
    # Action-oriented
    "act": {
        "name": "Take Action",
        "description": "Something needs to be done immediately or soon",
        "triggers": ["task", "todo", "complete", "finish", "deadline", "urgent"],
        "agent_3_action": "create_task"
    },
    "schedule": {
        "name": "Schedule Event",
        "description": "Time-based appointment or meeting",
        "triggers": ["meeting", "appointment", "at", "pm", "am", "schedule"],
        "agent_3_action": "create_calendar_event"
    },
    "pay": {
        "name": "Make Payment",
        "description": "Bill or payment due",
        "triggers": ["bill", "due", "payment", "invoice", "pay by"],
        "agent_3_action": "add_to_bills"
    },
    "buy": {
        "name": "Purchase Item",
        "description": "Shopping or buying decision",
        "triggers": ["buy", "purchase", "order", "cart", "price"],
        "agent_3_action": "add_to_shopping_list"
    },
    
    # Information-oriented
    "remember": {
        "name": "Remember/Save",
        "description": "Information to store for later",
        "triggers": ["save", "remember", "bookmark", "keep"],
        "agent_3_action": "create_note"
    },
    "learn": {
        "name": "Learn/Study",
        "description": "Educational content to study",
        "triggers": ["learn", "study", "understand", "tutorial", "course"],
        "agent_3_action": "create_note_and_find_resources"
    },
    "track": {
        "name": "Track/Monitor",
        "description": "Ongoing monitoring or tracking",
        "triggers": ["track", "monitor", "status", "progress"],
        "agent_3_action": "create_tracker_entry"
    },
    "reference": {
        "name": "Reference Material",
        "description": "Documentation or reference to keep",
        "triggers": ["documentation", "reference", "guide", "manual"],
        "agent_3_action": "create_note"
    },
    
    # Research-oriented
    "research": {
        "name": "Research/Investigate",
        "description": "Needs investigation or deep research",
        "triggers": ["error", "bug", "not working", "investigate", "find out"],
        "agent_3_action": "trigger_research_agent"
    },
    "compare": {
        "name": "Compare Options",
        "description": "Need to evaluate multiple options",
        "triggers": ["compare", "vs", "which one", "better", "options"],
        "agent_3_action": "create_comparison_note"
    },
    
    # Follow-up oriented
    "follow_up": {
        "name": "Follow Up Later",
        "description": "Requires future action or check-in",
        "triggers": ["follow up", "check back", "remind me", "later"],
        "agent_3_action": "create_reminder"
    },
    "wait": {
        "name": "Waiting For",
        "description": "Waiting for response or action from others",
        "triggers": ["waiting for", "pending", "awaiting"],
        "agent_3_action": "create_waiting_item"
    },
    
    # Low priority
    "archive": {
        "name": "Just Archive",
        "description": "Save for records, no action needed",
        "triggers": ["fyi", "for your information", "receipt", "confirmation"],
        "agent_3_action": "archive_only"
    },
    "ignore": {
        "name": "No Action Needed",
        "description": "Informational only, no follow-up",
        "triggers": ["just noting", "informational"],
        "agent_3_action": "skip"
    }
}

# ============================================
# DOMAIN-SPECIFIC INTENTS MAPPING
# ============================================

DOMAIN_LIKELY_INTENTS = {
    "work_career": ["act", "schedule", "research", "remember", "follow_up"],
    "education_learning": ["learn", "act", "schedule", "reference", "research"],
    "money_finance": ["pay", "track", "remember", "schedule", "archive"],
    "home_daily_life": ["buy", "act", "track", "schedule", "remember"],
    "health_wellbeing": ["schedule", "track", "remember", "act", "follow_up"],
    "family_relationships": ["schedule", "remember", "act", "track"],
    "travel_movement": ["schedule", "remember", "track", "buy", "reference"],
    "shopping_consumption": ["buy", "compare", "remember", "track"],
    "entertainment_leisure": ["remember", "schedule", "buy", "track"],
    "social_community": ["remember", "reference", "archive"],
    "admin_documents": ["archive", "remember", "act", "schedule"],
    "ideas_thoughts": ["remember", "act", "archive"]
}

# ============================================
# NEW FIRESTORE COLLECTIONS (By Domain)
# ============================================

DOMAIN_COLLECTIONS = {
    "work_career": "work_items",           # Tasks, meetings, job apps
    "education_learning": "learning_items", # Courses, assignments
    "money_finance": "financial_items",     # Bills, payments, subscriptions
    "home_daily_life": "home_items",        # Chores, repairs, groceries
    "health_wellbeing": "health_items",     # Appointments, meds, workouts
    "family_relationships": "family_items",  # Events, school, birthdays
    "travel_movement": "travel_items",      # Bookings, itineraries, visas
    "shopping_consumption": "shopping_lists", # Already exists
    "entertainment_leisure": "media_items",  # Watchlist, events, books
    "social_community": "social_items",     # Posts, discussions, news
    "admin_documents": "document_items",    # IDs, forms, legal
    "ideas_thoughts": "notes"               # Already exists
}