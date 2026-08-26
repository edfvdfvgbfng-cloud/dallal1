"""
Smart Recommendations with Diversification
Provides personalized, diversified recommendations based on user preferences and context
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from dataclasses import dataclass
from collections import defaultdict
import random

from .ai_goal_understanding import UserGoal, GoalType
from .ai_constraint_engine import ConstraintEngine
from .ai_semantic_memory import SemanticMemory, MemoryType, MemoryImportance

logger = logging.getLogger(__name__)


class RecommendationCategory(Enum):
    """Categories for recommendation diversification"""
    BEST_BUDGET_FIT = "best_budget_fit"
    BEST_LOCATION_FIT = "best_location_fit"
    BEST_SPACE_FIT = "best_space_fit"
    BEST_OVERALL = "best_overall"
    BEST_VALUE = "best_value"
    MOST_COMPLETE = "most_complete"
    HIGHEST_QUALITY = "highest_quality"
    NEWEST = "newest"
    POPULAR = "popular"


@dataclass
class Recommendation:
    """Individual recommendation with category and score"""
    item: Dict[str, Any]
    category: RecommendationCategory
    score: float
    match_reasons: List[str]
    diversity_score: float
    rank: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'item': self.item,
            'category': self.category.value,
            'score': self.score,
            'match_reasons': self.match_reasons,
            'diversity_score': self.diversity_score,
            'rank': self.rank
        }


class SmartRecommendationEngine:
    """
    Advanced recommendation engine with diversification
    Provides balanced recommendations across multiple categories
    """
    
    def __init__(self):
        self.semantic_memory = SemanticMemory()
        self.constraint_engine = ConstraintEngine()
        self.category_weights = self._initialize_category_weights()
        self.diversity_threshold = 0.7
    
    def generate_recommendations(self, 
                                 user_goal: UserGoal,
                                 available_items: List[Dict],
                                 user_id: int = None,
                                 count: int = 10) -> List[Recommendation]:
        """
        Generate diversified recommendations
        
        Args:
            user_goal: User's goal and preferences
            available_items: Available items to recommend
            user_id: User ID for personalization
            count: Number of recommendations to generate
            
        Returns:
            List of diversified recommendations
        """
        try:
            if not available_items:
                return []
            
            # Get user preferences from memory
            user_preferences = self._get_user_preferences(user_id) if user_id else {}
            
            # Apply constraints to filter items
            filtered_items = self._apply_constraints(available_items, user_goal)
            
            if not filtered_items:
                return []
            
            # Calculate base scores for all items
            scored_items = self._calculate_base_scores(filtered_items, user_goal, user_preferences)
            
            # Generate category-based recommendations
            category_recommendations = self._generate_category_recommendations(
                scored_items, user_goal, user_preferences
            )
            
            # Apply diversification
            diversified_recommendations = self._apply_diversification(
                category_recommendations, count
            )
            
            # Assign final ranks
            for i, rec in enumerate(diversified_recommendations):
                rec.rank = i + 1
            
            logger.info(f"Generated {len(diversified_recommendations)} diversified recommendations")
            return diversified_recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def _get_user_preferences(self, user_id: int) -> Dict:
        """Get user preferences from semantic memory"""
        if not user_id:
            return {}
        
        return self.semantic_memory.get_user_preferences(user_id)
    
    def _apply_constraints(self, items: List[Dict], user_goal: UserGoal) -> List[Dict]:
        """Apply user constraints to filter items"""
        # Build constraint set from user goal
        constraint_set = self.constraint_engine.build_constraint_set_from_goal(user_goal)
        
        # Filter items
        filtered_items = []
        for item in items:
            if (constraint_set.matches_all_hard_constraints(item) and
                constraint_set.matches_forbidden_constraints(item)):
                filtered_items.append(item)
        
        return filtered_items
    
    def _calculate_base_scores(self, 
                              items: List[Dict],
                              user_goal: UserGoal,
                              user_preferences: Dict) -> List[Tuple[Dict, float]]:
        """Calculate base match scores for items"""
        scored_items = []
        
        for item in items:
            score = 0.0
            
            # Score based on user goal entities
            if user_goal.entities.get('governorate') == item.get('governorate'):
                score += 0.25
            
            if user_goal.entities.get('property_type') == item.get('property_type'):
                score += 0.20
            
            # Score based on budget
            if user_goal.entities.get('price'):
                max_price = user_goal.entities['price']
                if isinstance(max_price, dict):
                    max_price = max_price.get('max', max_price)
                
                item_price = item.get('price', 0)
                if item_price <= max_price:
                    # Better score for items closer to max price but under budget
                    budget_fit = 1.0 - (item_price / max_price) * 0.5
                    score += 0.25 * budget_fit
            
            # Score based on preferences
            for preference in user_goal.preferences:
                if preference == 'quiet' and item.get('quiet_area'):
                    score += 0.10
                if preference == 'near_schools' and item.get('near_schools'):
                    score += 0.10
                if preference == 'new' and item.get('is_new'):
                    score += 0.05
            
            # Score based on user preferences from memory
            if user_preferences.get('preferred_districts'):
                if item.get('district') in user_preferences['preferred_districts']:
                    score += 0.15
            
            if user_preferences.get('price_range'):
                pref_min, pref_max = user_preferences['price_range']
                item_price = item.get('price', 0)
                if pref_min <= item_price <= pref_max:
                    score += 0.10
            
            # Normalize score
            score = min(score, 1.0)
            
            scored_items.append((item, score))
        
        return scored_items
    
    def _generate_category_recommendations(self, 
                                         scored_items: List[Tuple[Dict, float]],
                                         user_goal: UserGoal,
                                         user_preferences: Dict) -> Dict[RecommendationCategory, List[Recommendation]]:
        """Generate recommendations for each category"""
        category_recommendations = defaultdict(list)
        
        if not scored_items:
            return category_recommendations
        
        # Sort by base score
        scored_items.sort(key=lambda x: x[1], reverse=True)
        
        # BEST_BUDGET_FIT
        budget_fits = []
        for item, score in scored_items:
            if user_goal.entities.get('price'):
                rec = Recommendation(
                    item=item,
                    category=RecommendationCategory.BEST_BUDGET_FIT,
                    score=score,
                    match_reasons=['ضمن الميزانية'],
                    diversity_score=0.0
                )
                budget_fits.append(rec)
        category_recommendations[RecommendationCategory.BEST_BUDGET_FIT] = budget_fits[:3]
        
        # BEST_LOCATION_FIT
        location_fits = []
        for item, score in scored_items:
            if user_goal.entities.get('governorate') == item.get('governorate'):
                rec = Recommendation(
                    item=item,
                    category=RecommendationCategory.BEST_LOCATION_FIT,
                    score=score,
                    match_reasons=['الموقع المطلوب'],
                    diversity_score=0.0
                )
                location_fits.append(rec)
        category_recommendations[RecommendationCategory.BEST_LOCATION_FIT] = location_fits[:3]
        
        # BEST_SPACE_FIT
        space_fits = []
        for item, score in scored_items:
            if user_goal.entities.get('area'):
                rec = Recommendation(
                    item=item,
                    category=RecommendationCategory.BEST_SPACE_FIT,
                    score=score,
                    match_reasons=['المساحة مناسبة'],
                    diversity_score=0.0
                )
                space_fits.append(rec)
        category_recommendations[RecommendationCategory.BEST_SPACE_FIT] = space_fits[:3]
        
        # BEST_OVERALL
        overall_fits = []
        for item, score in scored_items[:5]:
            rec = Recommendation(
                item=item,
                category=RecommendationCategory.BEST_OVERALL,
                score=score,
                match_reasons=['أعلى تطابق عام'],
                diversity_score=0.0
            )
            overall_fits.append(rec)
        category_recommendations[RecommendationCategory.BEST_OVERALL] = overall_fits
        
        # BEST_VALUE (price per square meter)
        value_fits = []
        for item, score in scored_items:
            if item.get('price') and item.get('area'):
                price_per_m2 = item['price'] / item['area']
                rec = Recommendation(
                    item=item,
                    category=RecommendationCategory.BEST_VALUE,
                    score=score,
                    match_reasons=[f'قيمة ممتازة ({price_per_m2:.0f}/متر)'],
                    diversity_score=0.0
                )
                value_fits.append(rec)
        value_fits.sort(key=lambda x: x.item.get('price', float('inf')))
        category_recommendations[RecommendationCategory.BEST_VALUE] = value_fits[:3]
        
        # MOST_COMPLETE (data quality)
        complete_fits = []
        for item, score in scored_items:
            completeness = self._calculate_completeness(item)
            rec = Recommendation(
                item=item,
                category=RecommendationCategory.MOST_COMPLETE,
                score=score,
                match_reasons=[f'معلومات كاملة ({completeness:.0%})'],
                diversity_score=0.0
            )
            complete_fits.append(rec)
        complete_fits.sort(key=lambda x: x.item.get('completeness', 0), reverse=True)
        category_recommendations[RecommendationCategory.MOST_COMPLETE] = complete_fits[:3]
        
        # NEWEST
        newest_fits = []
        for item, score in scored_items:
            if item.get('created_at'):
                rec = Recommendation(
                    item=item,
                    category=RecommendationCategory.NEWEST,
                    score=score,
                    match_reasons=['أحدث العقارات'],
                    diversity_score=0.0
                )
                newest_fits.append(rec)
        newest_fits.sort(key=lambda x: x.item.get('created_at', ''), reverse=True)
        category_recommendations[RecommendationCategory.NEWEST] = newest_fits[:2]
        
        return category_recommendations
    
    def _calculate_completeness(self, item: Dict) -> float:
        """Calculate data completeness score for an item"""
        required_fields = ['title', 'price', 'area', 'governorate', 'description']
        optional_fields = ['district', 'property_type', 'images', 'amenities']
        
        required_count = sum(1 for field in required_fields if item.get(field))
        optional_count = sum(1 for field in optional_fields if item.get(field))
        
        completeness = (required_count / len(required_fields) * 0.7) + \
                     (optional_count / len(optional_fields) * 0.3)
        
        return completeness
    
    def _apply_diversification(self, 
                             category_recommendations: Dict[RecommendationCategory, List[Recommendation]],
                             count: int) -> List[Recommendation]:
        """Apply diversification to avoid similar recommendations"""
        final_recommendations = []
        used_item_ids = set()
        
        # Sort categories by weight
        sorted_categories = sorted(
            category_recommendations.items(),
            key=lambda x: self.category_weights.get(x[0].value, 1.0),
            reverse=True
        )
        
        # Select items from each category
        for category, recommendations in sorted_categories:
            if len(final_recommendations) >= count:
                break
            
            category_weight = self.category_weights.get(category.value, 1.0)
            category_count = max(1, int(count * category_weight / 10))
            
            selected_count = 0
            for rec in recommendations:
                if selected_count >= category_count:
                    break
                
                item_id = rec.item.get('id')
                if item_id not in used_item_ids:
                    # Calculate diversity score
                    rec.diversity_score = self._calculate_diversity_score(rec, final_recommendations)
                    
                    # Only add if diversity score is above threshold
                    if rec.diversity_score >= self.diversity_threshold or len(final_recommendations) < count // 2:
                        final_recommendations.append(rec)
                        used_item_ids.add(item_id)
                        selected_count += 1
        
        # Fill remaining slots with highest scoring items
        if len(final_recommendations) < count:
            all_recommendations = [rec for recs in category_recommendations.values() for rec in recs]
            all_recommendations.sort(key=lambda x: x.score, reverse=True)
            
            for rec in all_recommendations:
                if len(final_recommendations) >= count:
                    break
                
                item_id = rec.item.get('id')
                if item_id not in used_item_ids:
                    final_recommendations.append(rec)
                    used_item_ids.add(item_id)
        
        # Sort by final rank (diversity + score)
        final_recommendations.sort(key=lambda x: (x.score + x.diversity_score) / 2, reverse=True)
        
        return final_recommendations[:count]
    
    def _calculate_diversity_score(self, 
                                  recommendation: Recommendation,
                                  existing_recommendations: List[Recommendation]) -> float:
        """Calculate diversity score compared to existing recommendations"""
        if not existing_recommendations:
            return 1.0
        
        diversity_score = 1.0
        item = recommendation.item
        
        for existing_rec in existing_recommendations:
            existing_item = existing_rec.item
            
            # Calculate similarity
            similarity = self._calculate_similarity(item, existing_item)
            
            # Reduce diversity score based on similarity
            diversity_score -= similarity * 0.3
        
        return max(diversity_score, 0.0)
    
    def _calculate_similarity(self, item1: Dict, item2: Dict) -> float:
        """Calculate similarity between two items"""
        similarity = 0.0
        
        # Location similarity
        if item1.get('governorate') == item2.get('governorate'):
            similarity += 0.3
            if item1.get('district') == item2.get('district'):
                similarity += 0.2
        
        # Type similarity
        if item1.get('property_type') == item2.get('property_type'):
            similarity += 0.2
        
        # Price similarity
        price1 = item1.get('price', 0)
        price2 = item2.get('price', 0)
        if price1 and price2:
            price_ratio = min(price1, price2) / max(price1, price2)
            similarity += price_ratio * 0.2
        
        # Area similarity
        area1 = item1.get('area', 0)
        area2 = item2.get('area', 0)
        if area1 and area2:
            area_ratio = min(area1, area2) / max(area1, area2)
            similarity += area_ratio * 0.1
        
        return min(similarity, 1.0)
    
    def _initialize_category_weights(self) -> Dict[str, float]:
        """Initialize weights for recommendation categories"""
        return {
            'best_overall': 3.0,
            'best_budget_fit': 2.5,
            'best_location_fit': 2.0,
            'best_space_fit': 1.5,
            'best_value': 2.0,
            'most_complete': 1.5,
            'newest': 1.0,
            'popular': 1.0
        }
    
    def explain_recommendation(self, recommendation: Recommendation) -> str:
        """Generate explanation for why this item was recommended"""
        explanation_parts = []
        
        # Add category explanation
        category_explanations = {
            RecommendationCategory.BEST_BUDGET_FIT: "هذا الخيار مناسب لميزانيتك",
            RecommendationCategory.BEST_LOCATION_FIT: "هذا الخيار في الموقع المطلوب",
            RecommendationCategory.BEST_SPACE_FIT: "هذا الخيار يمتلك المساحة المناسبة",
            RecommendationCategory.BEST_OVERALL: "هذا الخيار يحتوي أعلى تطابق عام مع طلبك",
            RecommendationCategory.BEST_VALUE: "هذا الخيار يمتلك قيمة ممتازة مقارنة بالسعر",
            RecommendationCategory.MOST_COMPLETE: "هذا الخيار يمتلك معلومات كاملة",
            RecommendationCategory.NEWEST: "هذا الخيار من أحدث العقارات المتوفرة"
        }
        
        category_explanation = category_explanations.get(recommendation.category, "")
        if category_explanation:
            explanation_parts.append(category_explanation)
        
        # Add match reasons
        if recommendation.match_reasons:
            explanation_parts.append("، ".join(recommendation.match_reasons))
        
        # Add score explanation
        if recommendation.score > 0.8:
            explanation_parts.append(f"(تطابق {recommendation.score:.0%})")
        
        return " ".join(explanation_parts) if explanation_parts else "موصى به بناءً على تفضيلاتك"
    
    def get_recommendation_summary(self, recommendations: List[Recommendation]) -> Dict:
        """Get summary of recommendations"""
        if not recommendations:
            return {'total': 0, 'categories': {}}
        
        category_counts = defaultdict(int)
        score_stats = []
        
        for rec in recommendations:
            category_counts[rec.category.value] += 1
            score_stats.append(rec.score)
        
        return {
            'total': len(recommendations),
            'categories': dict(category_counts),
            'average_score': sum(score_stats) / len(score_stats) if score_stats else 0,
            'score_range': (min(score_stats), max(score_stats)) if score_stats else (0, 0)
        }
    
    def adjust_for_counterfactual(self, 
                                 recommendations: List[Recommendation],
                                 relaxation_suggestions: List[Dict]) -> List[Recommendation]:
        """Adjust recommendations based on counterfactual suggestions"""
        if not relaxation_suggestions:
            return recommendations
        
        # If we have relaxation suggestions, mention them in recommendations
        adjusted_recommendations = []
        
        for rec in recommendations:
            # Check if this recommendation would be affected by relaxation
            rec_copy = Recommendation(
                item=rec.item.copy(),
                category=rec.category,
                score=rec.score,
                match_reasons=rec.match_reasons.copy(),
                diversity_score=rec.diversity_score
            )
            
            # Add note about potential relaxation
            for suggestion in relaxation_suggestions:
                if suggestion.get('constraint') and self._would_benefit_from_relaxation(
                    rec.item, suggestion['constraint']
                ):
                    rec_copy.match_reasons.append(
                        f"قد تظهر خيارات أفضل إذا {suggestion.get('reason', '')}"
                    )
            
            adjusted_recommendations.append(rec_copy)
        
        return adjusted_recommendations
    
    def _would_benefit_from_relaxation(self, item: Dict, constraint: Dict) -> bool:
        """Check if item would benefit from constraint relaxation"""
        constraint_field = constraint.get('field')
        constraint_value = constraint.get('value')
        
        if constraint_field == 'budget' and constraint_value:
            item_price = item.get('price', 0)
            if item_price > constraint_value:
                return True
        
        if constraint_field == 'location' and constraint_value:
            item_location = item.get('governorate')
            if item_location != constraint_value:
                return True
        
        return False


# Global instance
smart_recommendation_engine = SmartRecommendationEngine()