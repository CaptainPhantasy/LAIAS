# Indiana SMB Business Development Agent

## Overview

The Indiana SMB Business Development Agent is a specialized 6-agent system designed to help solo developers acquire clients in the Indiana SMB market. It focuses on generating leads for custom software solutions, website design, and AI integration services.

## Architecture

The agent follows the Godzilla pattern with 6 specialized agents working in sequence:

1. **Market Research Specialist** - Identifies high-value prospects in Indiana SMB market
2. **Personalized Content Specialist** - Creates customized outreach content for each prospect
3. **Multi-Channel Outreach Specialist** - Executes systematic outreach campaigns
4. **Relationship Building Specialist** - Qualifies leads using BANT framework
5. **Proposal Development Specialist** - Creates compelling proposals and closes deals
6. **Metrics Analyst** - Analyzes campaign performance and optimizes strategies

## Key Features

- **Targeted Market Research**: Focuses on Indiana SMBs in key industries (Healthcare, Manufacturing, Legal, Agriculture, Professional Services, Retail, Education)
- **Personalized Outreach**: Creates customized content for each prospect addressing specific pain points
- **Multi-Channel Approach**: Uses email, LinkedIn, and phone outreach strategically
- **Qualification Framework**: Uses BANT (Budget, Authority, Need, Timeline) to qualify leads
- **Proposal Generation**: Creates compelling proposals with clear ROI and implementation plans
- **Performance Analytics**: Tracks key metrics and optimizes for continuous improvement

## How to Use

### Prerequisites

- LAIAS platform installed and running
- Valid API keys for LLM provider (OpenAI, ZAI, etc.)
- Optional: SERPER_API_KEY for enhanced search capabilities

### Running the Agent

```bash
cd /Volumes/Storage/LAIAS
python -m agents.indiana_smb_business_development
```

### Configuration

The agent can be configured by modifying the initial parameters:

- `target_industries`: Modify the list of target industries
- `target_geography`: Adjust the geographic focus area
- `output_directory`: Change where results are saved

## Expected Outcomes

After running the agent, you can expect:

1. **Market Research Report**: Comprehensive analysis of Indiana SMB market with 50-100 high-potential prospects
2. **Personalized Content Pack**: Customized emails, LinkedIn messages, and follow-up sequences for each prospect
3. **Outreach Campaign Plan**: Systematic multi-channel campaign with scheduling and tracking
4. **Qualified Lead Pipeline**: Prospects qualified using BANT framework with detailed profiles
5. **Compelling Proposals**: Ready-to-present proposals for qualified leads
6. **Performance Metrics**: Analysis of campaign effectiveness with optimization recommendations

## Integration with Other Systems

The agent integrates seamlessly with:

- **LAIAS Marketing Crew**: Use generated content for broader marketing campaigns
- **Website Factory**: Create client-specific websites as part of proposals
- **CRM Systems**: Export leads and tracking data for follow-up

## Customization

The agent can be easily customized for different:

- Geographic regions
- Industry verticals
- Service offerings
- Outreach strategies
- Qualification criteria

## Results Tracking

The agent automatically tracks and reports on:

- Leads generated
- Outreach attempts and responses
- Qualified leads
- Closed deals
- Revenue generated
- Conversion rates by channel
- ROI metrics

## Best Practices

1. **Run Regularly**: Execute monthly to maintain a healthy pipeline
2. **Monitor Performance**: Review metrics regularly and adjust strategies
3. **Follow Up**: Use the agent's outputs as a foundation for personal follow-up
4. **Iterate**: Use insights to refine targeting and messaging over time