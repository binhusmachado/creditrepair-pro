from typing import Dict, List, Any
from datetime import datetime, timedelta
from config import settings
import logging

logger = logging.getLogger(__name__)

class StrategyBuilder:
    """Build comprehensive dispute strategies"""
    
    def __init__(self):
        self.strategies = {
            "factual_dispute": {
                "name": "Factual Dispute",
                "description": "Direct dispute of factual inaccuracies",
                "timeline_days": 30,
                "success_rate": 0.65,
                "intensity": "standard"
            },
            "section_609": {
                "name": "Section 609 Verification",
                "description": "Request verification under FCRA § 609",
                "timeline_days": 30,
                "success_rate": 0.75,
                "intensity": "standard"
            },
            "section_605b": {
                "name": "Section 605B Identity Theft Block",
                "description": "Block fraudulent accounts under FCRA § 605B",
                "timeline_days": 4,
                "success_rate": 0.90,
                "intensity": "urgent"
            },
            "debt_validation": {
                "name": "Debt Validation Request",
                "description": "Request validation under FDCPA § 809",
                "timeline_days": 30,
                "success_rate": 0.70,
                "intensity": "firm"
            },
            "goodwill_adjustment": {
                "name": "Goodwill Adjustment",
                "description": "Request goodwill deletion",
                "timeline_days": 14,
                "success_rate": 0.40,
                "intensity": "polite"
            },
            "fcra_violation": {
                "name": "FCRA Violation Challenge",
                "description": "Challenge based on FCRA violations",
                "timeline_days": 30,
                "success_rate": 0.80,
                "intensity": "aggressive"
            },
            "method_of_verification": {
                "name": "Method of Verification Request",
                "description": "Request verification method under FCRA § 611(a)(7)",
                "timeline_days": 15,
                "success_rate": 0.60,
                "intensity": "firm"
            }
        }
    
    def build_strategy(self, errors: List[Dict], client_data: Dict, round_number: int = 1) -> Dict:
        """Build complete dispute strategy"""
        
        # Organize into rounds
        rounds = self._organize_rounds(errors, round_number)
        
        # Create timeline
        timeline = self._create_timeline(rounds, round_number)
        
        # Generate step-by-step guide
        guide = self._generate_guide(rounds, round_number)
        
        # Calculate score improvement estimates
        estimates = self._calculate_estimates(errors)
        
        return {
            "client_id": client_data.get("id"),
            "current_round": round_number,
            "total_rounds": len(rounds),
            "rounds": rounds,
            "timeline": timeline,
            "guide": guide,
            "estimated_improvement": estimates,
            "preparation_checklist": self._generate_checklist(rounds),
            "tips_and_warnings": self._generate_tips(round_number),
            "bureau_addresses": settings.BUREAU_INFO
        }
    
    def _organize_rounds(self, errors: List[Dict], start_round: int) -> List[Dict]:
        """Organize errors into dispute rounds"""
        rounds = []
        
        # Sort by priority
        sorted_errors = sorted(errors, key=lambda x: (x.get("priority", 5), -x.get("estimated_impact", 0)))
        
        # Group by bureau
        by_bureau = {"equifax": [], "experian": [], "transunion": []}
        for error in sorted_errors:
            # Assign to all bureaus if cross-bureau
            if error.get("type") == "cross_bureau_discrepancy":
                for bureau in by_bureau:
                    by_bureau[bureau].append(error)
            else:
                # Assign based on strategy or default to all
                for bureau in by_bureau:
                    by_bureau[bureau].append(error)
        
        # Create rounds (max 5 per bureau per round)
        round_num = start_round
        while any(len(items) > 0 for items in by_bureau.values()):
            current_round = {
                "round_number": round_num,
                "equifax": [],
                "experian": [],
                "transunion": []
            }
            
            for bureau in by_bureau:
                # Take up to 5 items for this bureau
                items = by_bureau[bureau][:5]
                by_bureau[bureau] = by_bureau[bureau][5:]
                
                for item in items:
                    current_round[bureau].append({
                        "error": item,
                        "strategy": self._get_strategy_details(item.get("dispute_strategy", "factual_dispute")),
                        "letter_type": self._get_letter_type(item),
                        "legal_basis": item.get("fcra_section", "623(a)(1)")
                    })
            
            rounds.append(current_round)
            round_num += 1
        
        return rounds
    
    def _create_timeline(self, rounds: List[Dict], start_round: int) -> List[Dict]:
        """Create timeline with dates"""
        timeline = []
        base_date = datetime.utcnow()
        
        for i, round_data in enumerate(rounds):
            round_num = start_round + i
            send_date = base_date + timedelta(days=i * 45)  # 45 days between rounds
            response_due = send_date + timedelta(days=30)
            follow_up = response_due + timedelta(days=7)
            
            timeline.append({
                "round": round_num,
                "send_date": send_date.strftime("%Y-%m-%d"),
                "response_deadline": response_due.strftime("%Y-%m-%d"),
                "follow_up_date": follow_up.strftime("%Y-%m-%d"),
                "bureaus": [b for b in ["equifax", "experian", "transunion"] 
                          if round_data.get(b)]
            })
        
        return timeline
    
    def _generate_guide(self, rounds: List[Dict], round_number: int) -> Dict:
        """Generate step-by-step guide"""
        return {
            "preparation": [
                "Gather all credit reports",
                "Review error analysis",
                "Print dispute letters",
                "Gather supporting documentation",
                "Prepare certified mail envelopes"
            ],
            "sending": [
                "Send letters via certified mail with return receipt",
                "Keep copies of everything sent",
                "Track delivery confirmation",
                "Mark calendar for response deadline"
            ],
            "waiting": [
                "Wait 30 days for bureau response",
                "Check mail daily for responses",
                "Do not dispute same items during waiting period"
            ],
            "response": [
                "Review all responses carefully",
                "Check for deleted/updated items",
                "Verify any remaining errors",
                "Prepare next round if needed"
            ],
            "follow_up": [
                "If no response by day 37, send follow-up",
                "Document all outcomes",
                "Update credit reports",
                "Plan next round strategy"
            ]
        }
    
    def _calculate_estimates(self, errors: List[Dict]) -> Dict:
        """Calculate estimated score improvement"""
        if not errors:
            return {"best": 0, "realistic": 0, "conservative": 0}
        
        total_impact = sum(e.get("estimated_impact", 0) for e in errors)
        
        return {
            "best": int(total_impact * 1.0),  # 100% of estimated
            "realistic": int(total_impact * 0.6),  # 60% success
            "conservative": int(total_impact * 0.3)  # 30% success
        }
    
    def _generate_checklist(self, rounds: List[Dict]) -> List[str]:
        """Generate preparation checklist"""
        return [
            "□ Review all error findings",
            "□ Print 3 copies of each letter",
            "□ Prepare certified mail (return receipt requested)",
            "□ Include copy of ID and proof of address",
            "□ Keep copies of everything for your records",
            "□ Mark calendar with response deadlines",
            "□ Set up mail tracking alerts",
            "□ Prepare follow-up calendar reminders"
        ]
    
    def _generate_tips(self, round_number: int) -> List[str]:
        """Generate tips and warnings"""
        tips = [
            "Never dispute online - use certified mail only",
            "Keep detailed records of all correspondence",
            "Don't dispute more than 5 items per bureau per round",
            "Wait for responses before sending next round"
        ]
        
        if round_number > 1:
            tips.extend([
                "Escalate tone in follow-up rounds",
                "Reference previous dispute attempts",
                "Consider FCRA violation claims if ignored"
            ])
        
        if round_number >= 3:
            tips.extend([
                "Consider CFPB complaint if bureaus don't respond",
                "Document all violations for potential legal action",
                "Consult attorney for repeated non-compliance"
            ])
        
        return tips
    
    def _get_strategy_details(self, strategy_key: str) -> Dict:
        """Get strategy details"""
        return self.strategies.get(strategy_key, self.strategies["factual_dispute"])
    
    def _get_letter_type(self, error: Dict) -> str:
        """Determine letter type for error"""
        strategy = error.get("dispute_strategy", "factual_dispute")
        error_type = error.get("type", "")
        
        if error_type in ["identity_theft", "not_my_account"]:
            return "section_605b"
        elif error_type in ["paid_collection", "medical_collection_ncap"]:
            return "debt_validation"
        elif error_type in ["unauthorized_inquiry"]:
            return "fcra_violation"
        elif strategy == "goodwill_adjustment":
            return "goodwill"
        else:
            return "bureau_dispute"