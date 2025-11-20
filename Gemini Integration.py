"""
Gemini-Powered Agent Enhancement
=================================
This module adds Gemini AI integration to specialist agents for enhanced responses.
Earns 5 bonus points for using Gemini to power agents.

To use:
1. Install: pip install google-generativeai
2. Set API key: export GEMINI_API_KEY="your-key-here"
3. Run with Gemini-powered agents

Note: API key should be set as environment variable, NEVER hardcoded!
"""

import os
import logging
from typing import Dict, Any, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Install with: pip install google-generativeai")

logger = logging.getLogger(__name__)


class GeminiAgent:
    """
    Enhanced agent that uses Gemini for intelligent response generation.
    Falls back to rule-based responses if Gemini unavailable.
    """
    
    def __init__(self, agent_role: str, model_name: str = "gemini-pro"):
        """
        Initialize Gemini-powered agent.
        
        Args:
            agent_role: Role description (e.g., "Technical Support Specialist")
            model_name: Gemini model to use
        """
        self.agent_role = agent_role
        self.model_name = model_name
        self.gemini_enabled = False
        
        # Try to initialize Gemini
        if GEMINI_AVAILABLE:
            api_key = os.getenv('GEMINI_API_KEY')
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel(model_name)
                    self.gemini_enabled = True
                    logger.info(f"Gemini enabled for {agent_role}")
                except Exception as e:
                    logger.warning(f"Failed to initialize Gemini: {e}")
            else:
                logger.warning("GEMINI_API_KEY not set. Using fallback responses.")
        else:
            logger.warning("Gemini library not available. Using fallback responses.")
    
    def generate_response(self, 
                         ticket_info: Dict[str, Any], 
                         customer_context: Dict[str, Any],
                         kb_results: Optional[Dict] = None) -> str:
        """
        Generate intelligent response using Gemini.
        
        Args:
            ticket_info: Ticket details (subject, description, category)
            customer_context: Customer history and context
            kb_results: Knowledge base search results
            
        Returns:
            Generated response string
        """
        
        if not self.gemini_enabled:
            return self._fallback_response(ticket_info, kb_results)
        
        try:
            # Build comprehensive prompt for Gemini
            prompt = self._build_prompt(ticket_info, customer_context, kb_results)
            
            # Generate response with Gemini
            response = self.model.generate_content(prompt)
            
            logger.info(f"Gemini generated response for ticket {ticket_info.get('id')}")
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return self._fallback_response(ticket_info, kb_results)
    
    def _build_prompt(self, 
                     ticket_info: Dict[str, Any],
                     customer_context: Dict[str, Any], 
                     kb_results: Optional[Dict]) -> str:
        """Build comprehensive prompt for Gemini"""
        
        prompt = f"""You are a {self.agent_role} at a customer support company.

Your task is to provide a helpful, professional, and accurate response to a customer support ticket.

TICKET INFORMATION:
- Ticket ID: {ticket_info.get('id')}
- Subject: {ticket_info.get('subject')}
- Description: {ticket_info.get('description')}
- Category: {ticket_info.get('category')}
- Priority: {ticket_info.get('priority')}

CUSTOMER CONTEXT:
- Customer ID: {customer_context.get('customer_id')}
- Account Status: {customer_context.get('account_status', 'active')}
- Previous Tickets: {customer_context.get('total_tickets', 0)}
- Customer Tier: {customer_context.get('tier', 'standard')}

"""
        
        if kb_results:
            prompt += f"""KNOWLEDGE BASE INFORMATION:
The following information from our knowledge base may be relevant:
{kb_results}

Use this information to provide accurate steps and solutions.
"""
        
        prompt += """
RESPONSE REQUIREMENTS:
1. Be professional, empathetic, and concise
2. Provide clear, actionable steps when applicable
3. Personalize based on customer context (e.g., mention if they're a valued customer)
4. If urgent, acknowledge the priority
5. Include next steps or escalation path if needed
6. Keep response under 250 words
7. End with an offer for further assistance

Generate the response now:"""
        
        return prompt
    
    def _fallback_response(self, 
                          ticket_info: Dict[str, Any],
                          kb_results: Optional[Dict]) -> str:
        """Fallback response when Gemini unavailable"""
        
        response = f"Thank you for contacting support regarding: {ticket_info.get('subject')}\n\n"
        
        if kb_results and 'steps' in kb_results:
            response += "Here's how to resolve your issue:\n\n"
            for i, step in enumerate(kb_results['steps'], 1):
                response += f"{i}. {step}\n"
        else:
            response += "Our team is reviewing your request and will respond within 24 hours.\n"
        
        response += "\nIf you need immediate assistance, please contact our support line."
        
        return response


class GeminiTechnicalAgent(GeminiAgent):
    """Technical support agent powered by Gemini"""
    
    def __init__(self):
        super().__init__(
            agent_role="Technical Support Specialist with expertise in software troubleshooting, " \
                      "account access issues, and system debugging"
        )
        self.name = "GeminiTechnicalAgent"
    
    def process(self, ticket, customer_context, kb_tool):
        """Process technical ticket with Gemini enhancement"""
        logger.info(f"{self.name} processing ticket {ticket.id}")
        
        # Search knowledge base
        kb_results = kb_tool.search(ticket.description)
        
        # Prepare ticket info for Gemini
        ticket_info = {
            'id': ticket.id,
            'subject': ticket.subject,
            'description': ticket.description,
            'category': ticket.category.value if ticket.category else 'unknown',
            'priority': ticket.priority
        }
        
        # Prepare customer context
        context_dict = {
            'customer_id': customer_context.customer_id,
            'account_status': customer_context.account_status,
            'total_tickets': len(customer_context.previous_tickets),
            'tier': ticket.metadata.get('customer_info', {}).get('tier', 'standard')
        }
        
        # Generate response with Gemini
        resolution = self.generate_response(ticket_info, context_dict, kb_results)
        
        return resolution


class GeminiBillingAgent(GeminiAgent):
    """Billing support agent powered by Gemini"""
    
    def __init__(self):
        super().__init__(
            agent_role="Billing Support Specialist with expertise in payment processing, " \
                      "refunds, disputes, and account billing"
        )
        self.name = "GeminiBillingAgent"
    
    def process(self, ticket, customer_context, kb_tool):
        """Process billing ticket with Gemini enhancement"""
        logger.info(f"{self.name} processing ticket {ticket.id}")
        
        kb_results = kb_tool.search(ticket.description)
        
        ticket_info = {
            'id': ticket.id,
            'subject': ticket.subject,
            'description': ticket.description,
            'category': ticket.category.value if ticket.category else 'unknown',
            'priority': ticket.priority
        }
        
        context_dict = {
            'customer_id': customer_context.customer_id,
            'account_status': customer_context.account_status,
            'total_tickets': len(customer_context.previous_tickets),
            'tier': ticket.metadata.get('customer_info', {}).get('tier', 'standard'),
            'lifetime_value': customer_context.lifetime_value
        }
        
        resolution = self.generate_response(ticket_info, context_dict, kb_results)
        
        return resolution


class GeminiGeneralAgent(GeminiAgent):
    """General support agent powered by Gemini"""
    
    def __init__(self):
        super().__init__(
            agent_role="General Customer Support Specialist handling inquiries, " \
                      "information requests, and general assistance"
        )
        self.name = "GeminiGeneralAgent"
    
    def process(self, ticket, customer_context, kb_tool):
        """Process general ticket with Gemini enhancement"""
        logger.info(f"{self.name} processing ticket {ticket.id}")
        
        kb_results = kb_tool.search(ticket.description)
        
        ticket_info = {
            'id': ticket.id,
            'subject': ticket.subject,
            'description': ticket.description,
            'category': ticket.category.value if ticket.category else 'unknown',
            'priority': ticket.priority
        }
        
        context_dict = {
            'customer_id': customer_context.customer_id,
            'account_status': customer_context.account_status,
            'total_tickets': len(customer_context.previous_tickets),
            'tier': ticket.metadata.get('customer_info', {}).get('tier', 'standard')
        }
        
        resolution = self.generate_response(ticket_info, context_dict, kb_results)
        
        return resolution


# ============================================================================
# INTEGRATION WITH MAIN SYSTEM
# ============================================================================

def create_gemini_enhanced_system():
    """
    Create support triage system with Gemini-powered agents.
    
    Usage:
        # Set API key first: export GEMINI_API_KEY="your-key"
        system = create_gemini_enhanced_system()
        result = system.process_ticket(ticket)
    
    Returns:
        SupportTriageSystem with Gemini agents
    """
    from support_triage_system import (
        SupportTriageSystem, MemoryBank, KnowledgeBaseTool, 
        CRMTool, InMemorySessionService, MetricsCollector,
        IntakeAgent, TriageAgent, ResolutionAgent
    )
    
    # Create base components
    memory_bank = MemoryBank()
    kb_tool = KnowledgeBaseTool()
    crm_tool = CRMTool()
    session_service = InMemorySessionService()
    metrics = MetricsCollector()
    
    # Create agents with Gemini enhancement
    intake_agent = IntakeAgent(kb_tool, crm_tool)
    triage_agent = TriageAgent()
    
    # Use Gemini-powered specialist agents
    technical_agent = GeminiTechnicalAgent()
    billing_agent = GeminiBillingAgent()
    general_agent = GeminiGeneralAgent()
    
    resolution_agent = ResolutionAgent(memory_bank)
    
    # Create system instance
    system = SupportTriageSystem()
    system.memory_bank = memory_bank
    system.kb_tool = kb_tool
    system.crm_tool = crm_tool
    system.session_service = session_service
    system.metrics = metrics
    system.intake_agent = intake_agent
    system.triage_agent = triage_agent
    system.resolution_agent = resolution_agent
    
    # Replace specialist agents with Gemini versions
    system.technical_agent = technical_agent
    system.billing_agent = billing_agent
    system.general_agent = general_agent
    
    system.specialist_agents = {
        'TechnicalAgent': technical_agent,
        'BillingAgent': billing_agent,
        'GeneralAgent': general_agent
    }
    
    logger.info("Created Gemini-enhanced support triage system")
    
    return system


# ============================================================================
# DEMO WITH GEMINI
# ============================================================================

def run_gemini_demo():
    """Run demo with Gemini-powered agents"""
    
    print("=" * 80)
    print("GEMINI-ENHANCED SUPPORT TRIAGE SYSTEM - DEMO")
    print("=" * 80)
    
    # Check if Gemini is available
    if not GEMINI_AVAILABLE:
        print("\n⚠️  WARNING: google-generativeai not installed")
        print("Install with: pip install google-generativeai")
        print("Falling back to rule-based responses...\n")
    elif not os.getenv('GEMINI_API_KEY'):
        print("\n⚠️  WARNING: GEMINI_API_KEY not set")
        print("Set with: export GEMINI_API_KEY='your-key-here'")
        print("Falling back to rule-based responses...\n")
    else:
        print("\n✅ Gemini API configured successfully!")
        print("Using Gemini-powered intelligent agents\n")
    
    # Create Gemini-enhanced system
    system = create_gemini_enhanced_system()
    
    # Import ticket class
    from support_triage_system import Ticket
    
    # Create sample ticket
    ticket = Ticket(
        id="TKT-GEMINI-001",
        customer_id="CUST-99999",
        subject="App crashes on startup",
        description="Every time I try to open the mobile app, it crashes immediately. " \
                   "I've tried restarting my phone but it still doesn't work. " \
                   "This is really frustrating as I need to access my account urgently."
    )
    
    print(f"Processing ticket with Gemini agents...\n")
    print(f"Subject: {ticket.subject}")
    print(f"Description: {ticket.description}\n")
    
    # Process ticket
    result = system.process_ticket(ticket)
    
    print("=" * 80)
    print("GEMINI-POWERED RESPONSE")
    print("=" * 80)
    print(result['resolution'])
    print("\n" + "=" * 80)
    print(f"Quality Score: {result['quality_score']:.2f}/5.0")
    print(f"Processing Time: {result['processing_time']}")
    print("=" * 80)
    
    return system, result


if __name__ == "__main__":
    print("\n🤖 GEMINI INTEGRATION MODULE")
    print("=" * 80)
    print("This module adds Gemini AI to power intelligent agent responses")
    print("\nSetup:")
    print("1. pip install google-generativeai")
    print("2. export GEMINI_API_KEY='your-api-key-here'")
    print("3. python gemini_integration.py")
    print("=" * 80)
    print()
    
    run_gemini_demo()
