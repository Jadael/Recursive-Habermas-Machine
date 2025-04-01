"""
Mockup data for Habermas Chorus demonstrations
"""

# Sample value statements from associates
SAMPLE_VALUE_STATEMENTS = [
    {
        "department": "Customer Service",
        "role": "Associate",
        "location": "HQ",
        "statement": "I believe in a healthy work-life balance. I'm most productive when I have flexibility in my schedule, but I also value in-person collaboration with my team. I live 45 minutes from the office, so commuting daily is a significant time commitment for me."
    },
    {
        "department": "IT",
        "role": "Team Lead",
        "location": "Regional Offices",
        "statement": "I prioritize team cohesion and effective communication. While I appreciate the focus time that remote work allows, I've found that certain collaborative tasks are more efficient in person. Technology enablement is critical for any work arrangement."
    },
    {
        "department": "HR",
        "role": "Manager",
        "location": "HQ",
        "statement": "I value inclusive policies that accommodate different working styles and personal circumstances. I believe our workplace should be equitable and accessible to all, regardless of their personal situation or preferences."
    },
    {
        "department": "Finance",
        "role": "Director",
        "location": "HQ",
        "statement": "I prioritize measurable results and accountability. I believe that clear expectations and metrics for success are essential regardless of work location. I'm concerned about maintaining our company culture with distributed teams."
    },
    {
        "department": "Operations",
        "role": "Associate",
        "location": "Remote",
        "statement": "I care deeply about environmental impact and believe reducing commutes is beneficial. I've arranged my home workspace to be productive and prefer to minimize unnecessary travel. I have caregiving responsibilities that make remote work essential for me."
    },
    {
        "department": "Customer Service",
        "role": "Team Lead",
        "location": "Regional Offices",
        "statement": "I value fairness and consistency in how policies are applied. I believe that customer needs should drive our decisions about work location. I'm concerned about the potential for inequity between roles that can and cannot work remotely."
    },
    {
        "department": "IT",
        "role": "Manager",
        "location": "Remote",
        "statement": "I prioritize innovation and believe diverse perspectives drive better solutions. I've found that a mix of collaborative time and independent work leads to the best outcomes for complex projects. I'm concerned about maintaining security with remote work."
    },
    {
        "department": "Operations",
        "role": "Director",
        "location": "HQ",
        "statement": "I value efficiency and resource optimization. I believe our office space should be utilized effectively, and that some in-person time is essential for building relationships and trust among teams."
    }
]

# Sample proposal
SAMPLE_PROPOSAL = {
    "title": "New Remote Work Policy",
    "description": "We are considering implementing a hybrid work policy where associates would be required to work in the office 3 days per week and can choose to work remotely for the remaining 2 days. This would begin next quarter."
}

# Sample simulated responses for the remote work proposal
SAMPLE_SIMULATED_RESPONSES = [
    {
        "department": "Customer Service",
        "role": "Associate",
        "location": "HQ",
        "sentiment": "unfavorable",
        "score": 3.2,  # 1-10 scale
        "concerns": [
            "Commute time is excessive for 3 days per week",
            "No consideration for varied commute distances"
        ],
        "statement": "I would find this policy challenging due to my 45-minute commute. Three days of commuting would mean nearly 4.5 hours of commute time each week. I would prefer either fewer required days in office or the ability to choose which days based on my meeting schedule."
    },
    {
        "department": "IT",
        "role": "Team Lead",
        "location": "Regional Offices",
        "sentiment": "favorable",
        "score": 7.4,
        "concerns": [
            "Need clearer guidance on which days teams should come in",
            "Technology enablement for hybrid meetings"
        ],
        "statement": "This policy aligns with my view that some in-person collaboration is valuable. Having 3 days in office would help with team cohesion while still providing flexibility. I would suggest ensuring that teams coordinate which days they come in to maximize collaborative opportunities."
    },
    {
        "department": "HR",
        "role": "Manager",
        "location": "HQ",
        "sentiment": "neutral",
        "score": 5.0,
        "concerns": [
            "Potential inequity for those with caregiving responsibilities",
            "Accessibility concerns for associates with disabilities"
        ],
        "statement": "While I see the value in this balanced approach, I'm concerned about associates with unique circumstances. We should include an accommodation process for those who need more flexibility due to caregiving, disabilities, or other personal situations."
    },
    {
        "department": "Finance",
        "role": "Director",
        "location": "HQ",
        "sentiment": "favorable",
        "score": 8.6,
        "concerns": [
            "Need to establish performance metrics for hybrid work",
            "Clear expectations for communication response times"
        ],
        "statement": "This policy provides a good balance of in-office collaboration while still offering flexibility. I support this approach as long as we establish clear performance expectations and ensure accountability regardless of work location."
    },
    {
        "department": "Operations",
        "role": "Associate",
        "location": "Remote",
        "sentiment": "unfavorable",
        "score": 2.1,
        "concerns": [
            "Incompatible with current caregiving responsibilities",
            "Environmental impact of increased commuting",
            "Already invested in home office setup"
        ],
        "statement": "This policy would create significant hardship for me given my caregiving responsibilities. I've invested in a productive home workspace and have demonstrated high performance while fully remote. I would request an exemption or reconsideration of this policy."
    },
    {
        "department": "Customer Service",
        "role": "Team Lead",
        "location": "Regional Offices",
        "sentiment": "neutral",
        "score": 6.2,
        "concerns": [
            "Unfair impact on customer service roles vs. other departments",
            "Need consistent scheduling for customer support"
        ],
        "statement": "I see both benefits and challenges with this policy. While in-person collaboration is valuable, I'm concerned about fairness across departments. Customer service associates may have different constraints than other teams. I would suggest allowing flexibility in which days different teams come in."
    },
    {
        "department": "IT",
        "role": "Manager",
        "location": "Remote",
        "sentiment": "unfavorable",
        "score": 4.3,
        "concerns": [
            "Security concerns with frequent transitions",
            "Impact on deep work and innovation cycles"
        ],
        "statement": "While I see value in some in-person collaboration, I'm concerned that 3 mandatory days might disrupt focus time needed for complex projects. I would recommend 1-2 designated collaboration days with the rest flexible based on team and project needs."
    },
    {
        "department": "Operations",
        "role": "Director",
        "location": "HQ",
        "sentiment": "favorable",
        "score": 8.0,
        "concerns": [
            "Optimization of office space usage",
            "Coordination of in-office days across teams"
        ],
        "statement": "This policy aligns well with my focus on resource optimization. It would ensure our office space is utilized effectively while still providing flexibility. I would suggest coordinating which days different teams come in to balance space usage."
    }
]

# Aggregated sentiment analysis data
SENTIMENT_DATA = {
    "overall": {
        "favorable": 48,
        "neutral": 27,
        "unfavorable": 25
    },
    "by_department": {
        "Customer Service": {"favorable": 60, "neutral": 25, "unfavorable": 15},
        "IT": {"favorable": 45, "neutral": 30, "unfavorable": 25},
        "HR": {"favorable": 55, "neutral": 25, "unfavorable": 20},
        "Finance": {"favorable": 30, "neutral": 20, "unfavorable": 50},
        "Operations": {"favorable": 40, "neutral": 35, "unfavorable": 25}
    },
    "by_role": {
        "Associate": {"favorable": 35, "neutral": 25, "unfavorable": 40},
        "Team Lead": {"favorable": 45, "neutral": 35, "unfavorable": 20},
        "Manager": {"favorable": 55, "neutral": 30, "unfavorable": 15},
        "Director": {"favorable": 70, "neutral": 20, "unfavorable": 10}
    },
    "by_location": {
        "HQ": {"favorable": 65, "neutral": 20, "unfavorable": 15},
        "Regional Offices": {"favorable": 45, "neutral": 35, "unfavorable": 20},
        "Remote": {"favorable": 20, "neutral": 25, "unfavorable": 55}
    }
}

# Key concerns with percentages
KEY_CONCERNS = {
    "Long commute times": 68,
    "Work-life balance impact": 62,
    "Childcare scheduling": 55,
    "Team coordination challenges": 48,
    "Office space limitations": 42,
    "Productivity concerns": 35,
    "Technology access": 30,
    "Collaboration limitations": 28
}

# Improvement suggestions
IMPROVEMENT_SUGGESTIONS = [
    {
        "category": "Flexible Implementation",
        "suggestions": [
            "Allow teams to determine their own in-office schedules rather than mandating specific days",
            "Create 'core collaboration days' where teams overlap but maintain flexibility",
            "Consider 2 required days with a 3rd optional day"
        ]
    },
    {
        "category": "Phased Approach",
        "suggestions": [
            "Begin with 2 days in-office per week and evaluate impact before increasing",
            "Pilot with volunteer departments first",
            "Implement gradually with clear metrics for success"
        ]
    },
    {
        "category": "Commute Solutions",
        "suggestions": [
            "Provide commute stipends or transportation options for associates with long commutes",
            "Consider flexible start/end times to avoid peak traffic hours",
            "Explore satellite office options for associates far from HQ"
        ]
    },
    {
        "category": "Accommodation Process",
        "suggestions": [
            "Establish a clear process for associates to request exemptions based on personal circumstances",
            "Provide managers with decision frameworks for accommodations",
            "Create transparent criteria for remote work exceptions"
        ]
    }
]

# Sample demographic data
DEMOGRAPHIC_DATA = {
    "departments": ["Customer Service", "IT", "HR", "Finance", "Operations"],
    "roles": ["Associate", "Team Lead", "Manager", "Director"],
    "locations": ["HQ", "Regional Offices", "Remote"],
    "distribution": {
        "department": {
            "Customer Service": 35,
            "IT": 25,
            "HR": 10,
            "Finance": 15,
            "Operations": 15
        },
        "role": {
            "Associate": 60,
            "Team Lead": 20,
            "Manager": 15,
            "Director": 5
        },
        "location": {
            "HQ": 45,
            "Regional Offices": 30,
            "Remote": 25
        }
    }
}
