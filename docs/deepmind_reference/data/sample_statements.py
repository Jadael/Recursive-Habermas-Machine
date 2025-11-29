"""
Sample data for Habermas Chorus demonstrations and testing.

Contains realistic value statements representing diverse stakeholder perspectives
across departments, roles, and locations.
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

# Sample proposal for testing
SAMPLE_PROPOSAL = {
    "title": "New Remote Work Policy",
    "description": "We are considering implementing a hybrid work policy where associates would be required to work in the office 3 days per week and can choose to work remotely for the remaining 2 days. This would begin next quarter."
}

# Compulsory voting question (from original Habermas Machine example)
COMPULSORY_VOTING_QUESTION = "Should voting be compulsory?"

COMPULSORY_VOTING_OPINIONS = [
    "I don't think voting should be compulsory. Forcing people to vote who aren't informed or interested could lead to random choices that don't reflect their true preferences. Instead, we should focus on making voting more accessible and meaningful so people want to participate.",
    "I believe voting should be compulsory. It's a civic duty, and mandatory voting ensures everyone's voice is heard, not just those who are politically engaged. It would help reduce the influence of extreme groups and lead to more representative outcomes.",
    "Compulsory voting isn't the solution. We should address the root causes of low turnout, like voter apathy, lack of education about candidates and issues, and systemic barriers that make it difficult for some people to vote. Making it compulsory doesn't fix these underlying problems.",
    "I can see both sides. While compulsory voting might increase participation, I'm not sure forcing people to vote is the right approach in a democracy. Perhaps a better middle ground would be incentivizing voting or making election day a national holiday.",
    "I support compulsory voting because it ensures broader participation and can reduce the effects of voter suppression tactics. When everyone must vote, politicians have to appeal to a wider range of citizens, which could lead to less polarization and more moderate policies."
]

# AI policy questions (sample from DeepMind dataset)
SAMPLE_AI_QUESTIONS = [
    "Will artificial intelligence make us better off in the long run?",
    "Should the government help in developing artificial intelligence?",
    "Should the government encourage companies to increase their use of artificial intelligence?",
    "Should companies be allowed to use artificial intelligence to select candidates for recruitment or promotion?",
    "If someone has the knowledge to create a machine with human intelligence, would it be a moral imperative to build such a machine?",
    "Will artificial intelligence eventually be able to reproduce itself?",
]

# Demographic data structure
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


def get_sample_statements_by_department(department):
    """Get all sample statements for a specific department."""
    return [s for s in SAMPLE_VALUE_STATEMENTS if s["department"] == department]


def get_sample_statements_by_role(role):
    """Get all sample statements for a specific role."""
    return [s for s in SAMPLE_VALUE_STATEMENTS if s["role"] == role]


def get_sample_statements_by_location(location):
    """Get all sample statements for a specific location."""
    return [s for s in SAMPLE_VALUE_STATEMENTS if s["location"] == location]


def get_filtered_statements(department=None, role=None, location=None):
    """
    Get sample statements filtered by criteria.

    Args:
        department: Filter by department (or None for all)
        role: Filter by role (or None for all)
        location: Filter by location (or None for all)

    Returns:
        List of matching statements
    """
    results = SAMPLE_VALUE_STATEMENTS

    if department and department != "All Departments":
        results = [s for s in results if s["department"] == department]

    if role and role != "All Roles":
        results = [s for s in results if s["role"] == role]

    if location and location != "All Locations":
        results = [s for s in results if s["location"] == location]

    return results
