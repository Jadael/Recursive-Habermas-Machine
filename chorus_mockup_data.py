"""
Mockup data for Habermas Chorus demonstrations
"""

# Sample value statements from associates
SAMPLE_VALUE_STATEMENTS = [
    {
        "department": "Customer Service",
        "role": "Associate",
        "location": "Remote",
        "statement": "I value clear communication and timely responses from leadership since I work remotely and sometimes feel disconnected from the team. Having predictable schedules is crucial for me to balance client interactions with my family responsibilities as a single parent. I appreciate managers who trust their team to deliver quality work without micromanagement. Regular recognition of good performance motivates me, especially since I don't have daily in-person interactions with my supervisors. I believe transparency about company changes and career advancement opportunities helps remote workers feel included and valued."
    },
    {
        "department": "HR",
        "role": "Manager",
        "location": "HQ",
        "statement": "As someone working at headquarters, I value cross-departmental collaboration that helps me understand the broader organizational impact of HR initiatives. I believe in creating an inclusive workplace where employees feel psychologically safe to express concerns and ideas. Having worked my way up from an associate position, I'm passionate about developing internal talent and creating clear promotion pathways. Work-life balance is essential to me—I've experienced burnout in previous roles and prioritize sustainable workloads for myself and my team. I appreciate organizational cultures that embrace continuous feedback and adaptation rather than static annual reviews."
    },
    {
        "department": "Operations",
        "role": "Team Lead",
        "location": "Regional Offices",
        "statement": "Working in a regional office, I value being the bridge between headquarters' strategic vision and our local implementation realities. My 90-minute commute means flexibility around start times is particularly important to me. I believe in hands-on leadership and making time to work alongside my team members during busy periods. Open communication about upcoming changes helps me prepare my team effectively and reduce resistance. I value learning opportunities that focus on practical skills I can immediately apply to improve our processes."
    },
    {
        "department": "IT",
        "role": "Director",
        "location": "Remote",
        "statement": "Leading a distributed IT team has taught me to value asynchronous communication tools that respect different time zones and working styles. I believe strongly in outcome-based performance metrics rather than time-logged or constant availability. Having team members with diverse cultural backgrounds has shown me the importance of explicit communication and documented expectations. As someone with ADHD, I appreciate workplaces that allow for focused work periods without constant interruptions. I value organizations that invest in cutting-edge technologies and continuous learning, as this keeps our skills relevant and our work engaging."
    },
    {
        "department": "Finance",
        "role": "Associate",
        "location": "HQ",
        "statement": "As a recently hired finance associate, I value mentorship and guidance from experienced colleagues who can help me understand company-specific practices. Clear documentation of processes is important to me as I'm still learning our systems. I appreciate having quiet spaces for focused work, especially during month-end close periods when accuracy is critical. Being part of a diverse team helps me gain different perspectives on financial challenges. I value a workplace that recognizes both collaborative achievements and individual contributions to team success."
    },
    {
        "department": "Customer Service",
        "role": "Director",
        "location": "Regional Offices",
        "statement": "Having managed customer service teams for 15 years, I value leadership that balances business metrics with agent wellbeing. I believe frontline staff deserve a voice in process improvements since they experience customer challenges directly. Our regional location means we sometimes feel overlooked in company-wide initiatives, so I appreciate leadership that makes an effort to include our perspective. As the parent of a child with special needs, workplace flexibility during family emergencies has been crucial for my career longevity. I value transparent communication about organizational changes that might affect our team structure or client relationships."
    },
    {
        "department": "IT",
        "role": "Team Lead",
        "location": "HQ",
        "statement": "Working at headquarters gives me valuable face-time with leadership, but I'm mindful to create equal opportunities for my remote team members. I value technological solutions that enhance collaboration rather than creating additional work. Having transitioned from another industry, I appreciate a culture that values diverse experience and fresh perspectives. Clear priorities and realistic timelines are important to me for maintaining both project quality and team morale. I believe in creating psychological safety where team members can admit mistakes and ask questions without fear of judgment."
    },
    {
        "department": "Operations",
        "role": "Manager",
        "location": "Remote",
        "statement": "Managing operations remotely has taught me to value robust documentation and transparent workflows visible to all team members. I believe in giving my team autonomy while maintaining clear accountability frameworks. As someone living in a rural area, reliable connectivity and IT support are essential for my effectiveness. I value a workplace that recognizes results over hours worked or location. Having experienced both traditional and flexible work arrangements, I'm committed to accommodating different working styles while maintaining operational excellence."
    },
    {
        "department": "HR",
        "role": "Associate",
        "location": "Regional Offices",
        "statement": "Working in our regional HR office has shown me the importance of policies that can adapt to local contexts while maintaining company-wide fairness. I value clear career development paths that don't require relocation to headquarters. As someone from a minority background, I appreciate workplaces that actively seek diverse perspectives in decision-making. I believe in balancing digital efficiency with human connection, especially when addressing sensitive employee concerns. Regular two-way feedback opportunities help me improve my performance and feel valued as a contributor."
    },
    {
        "department": "Finance",
        "role": "Director",
        "location": "HQ",
        "statement": "Leading a finance team at headquarters, I value the strategic partnership between finance and other departments to support informed decision-making. I believe in transparent communication about company performance and financial constraints. Having worked internationally, I appreciate workplaces that embrace diverse communication styles and approaches to problem-solving. As someone approaching retirement age, I value opportunities to mentor younger colleagues and create succession plans. I believe organizational health is best measured through both financial metrics and employee wellbeing indicators."
    },
    {
        "department": "Customer Service",
        "role": "Team Lead",
        "location": "Remote",
        "statement": "As a remote team lead with hearing difficulties, I value meetings that include clear agendas and written follow-ups. I believe in creating team connections through meaningful virtual interactions rather than forced social events. My experience working across time zones has shown me the importance of respecting boundaries and offline time. I value workplaces that judge performance on customer satisfaction and team cohesion rather than adherence to rigid protocols. Having a neurodivergent perspective has helped me develop unique problem-solving approaches that I'm encouraged to share."
    },
    {
        "department": "Finance",
        "role": "Manager",
        "location": "Regional Offices",
        "statement": "Working in our regional finance office, I value the balance between corporate standardization and local autonomy in financial processes. I believe in promoting financial literacy across departments to build better business partnerships. As a parent of teenagers, I appreciate flexibility around school events and family commitments. My commute through heavy traffic means I value the option to work remotely during adverse weather conditions. Having seen multiple reorganizations, I value transparent communication about organizational changes and honest discussions about how they might impact regional teams."
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
