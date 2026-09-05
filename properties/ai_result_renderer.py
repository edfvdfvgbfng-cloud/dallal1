"""
AI Result Renderer
Renders search results into formatted cards for display
Supports multiple content types with appropriate formatting
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ResultRenderer:
    """
    Renders search results into formatted cards
    Supports properties, hotels, resorts, jobs, services, auctions, and brokers
    """
    
    def __init__(self):
        self.emoji_map = {
            'property': '🏠',
            'hotel': '🏨',
            'resort_inside': '🏖️',
            'resort_outside': '🏖️',
            'job': '💼',
            'service': '🔧',
            'auction': '🔨',
            'broker': '👤',
        }
    
    def render_results(self, results: List[Dict]) -> List[Dict]:
        """
        Render search results into formatted cards
        
        Args:
            results: List of search results with item, score, type, url
            
        Returns:
            List of formatted result cards
        """
        rendered = []
        
        for result in results:
            item = result['item']
            score = result['score']
            result_type = result['type']
            url = result['url']
            
            card = self._render_card(item, result_type, score, url)
            rendered.append(card)
        
        return rendered
    
    def _render_card(self, item: Any, result_type: str, score: float, url: str) -> Dict:
        """Render a single result card based on type"""
        renderers = {
            'property': self._render_property_card,
            'hotel': self._render_hotel_card,
            'resort_inside': self._render_resort_card,
            'resort_outside': self._render_resort_card,
            'job': self._render_job_card,
            'service': self._render_service_card,
            'auction': self._render_auction_card,
            'broker': self._render_broker_card,
        }
        
        renderer = renderers.get(result_type, self._render_generic_card)
        return renderer(item, score, url)
    
    def _render_property_card(self, property_obj, score: float, url: str) -> Dict:
        """Render property result card"""
        card = {
            'type': 'property',
            'emoji': '🏠',
            'title': getattr(property_obj, 'display_title', 'عقار'),
            'url': url,
            'score': score,
            'fields': []
        }
        
        # Location
        if hasattr(property_obj, 'governorate') and property_obj.governorate:
            card['fields'].append({
                'label': '📍',
                'value': property_obj.governorate
            })
        elif hasattr(property_obj, 'city') and property_obj.city:
            card['fields'].append({
                'label': '📍',
                'value': property_obj.city
            })
        
        # Price
        if hasattr(property_obj, 'price') and property_obj.price:
            card['fields'].append({
                'label': '💰',
                'value': f"{property_obj.price:,} د.ع"
            })
        
        # Area
        if hasattr(property_obj, 'area') and property_obj.area:
            card['fields'].append({
                'label': '📐',
                'value': f"{property_obj.area} م²"
            })
        
        # Rooms
        if hasattr(property_obj, 'rooms') and property_obj.rooms:
            card['fields'].append({
                'label': '🛏️',
                'value': f"{property_obj.rooms} غرف"
            })
        
        # Purpose
        if hasattr(property_obj, 'purpose') and property_obj.purpose:
            purpose_map = {'sale': 'بيع', 'rent': 'إيجار', 'investment': 'استثمار'}
            card['fields'].append({
                'label': '🎯',
                'value': purpose_map.get(property_obj.purpose, property_obj.purpose)
            })
        
        # Match score
        card['fields'].append({
            'label': '⭐',
            'value': f"مطابقة: {score:.0%}"
        })
        
        # Actions
        card['actions'] = [
            {'label': '👁️ عرض المنشور', 'action': 'view', 'url': url},
        ]
        
        # Add broker contact if available
        if hasattr(property_obj, 'broker') and property_obj.broker:
            card['actions'].append({
                'label': '💬 مراسلة الدلال',
                'action': 'contact_broker',
                'broker_id': property_obj.broker.id
            })
        
        return card
    
    def _render_hotel_card(self, hotel_obj, score: float, url: str) -> Dict:
        """Render hotel result card"""
        card = {
            'type': 'hotel',
            'emoji': '🏨',
            'title': getattr(hotel_obj, 'name', 'فندق'),
            'url': url,
            'score': score,
            'fields': []
        }
        
        # Location
        if hasattr(hotel_obj, 'governorate') and hotel_obj.governorate:
            card['fields'].append({
                'label': '📍',
                'value': hotel_obj.governorate
            })
        elif hasattr(hotel_obj, 'city') and hotel_obj.city:
            card['fields'].append({
                'label': '📍',
                'value': hotel_obj.city
            })
        
        # Star rating
        if hasattr(hotel_obj, 'star_rating') and hotel_obj.star_rating:
            stars = '⭐' * hotel_obj.star_rating
            card['fields'].append({
                'label': '⭐',
                'value': stars
            })
        
        # Price range
        if hasattr(hotel_obj, 'price_range') and hotel_obj.price_range:
            price_map = {
                'economy': 'اقتصادي',
                'medium': 'متوسط',
                'luxury': 'فاخر',
                'budget': 'حسب الميزانية'
            }
            card['fields'].append({
                'label': '💰',
                'value': price_map.get(hotel_obj.price_range, hotel_obj.price_range)
            })
        
        # Match score
        card['fields'].append({
            'label': '⭐',
            'value': f"مطابقة: {score:.0%}"
        })
        
        # Actions
        card['actions'] = [
            {'label': '👁️ عرض الفندق', 'action': 'view', 'url': url},
        ]
        
        return card
    
    def _render_resort_card(self, resort_obj, score: float, url: str) -> Dict:
        """Render resort result card"""
        card = {
            'type': 'resort',
            'emoji': '🏖️',
            'title': getattr(resort_obj, 'name', 'منتجع'),
            'url': url,
            'score': score,
            'fields': []
        }
        
        # Location
        if hasattr(resort_obj, 'governorate') and resort_obj.governorate:
            card['fields'].append({
                'label': '📍',
                'value': resort_obj.governorate
            })
        elif hasattr(resort_obj, 'city') and resort_obj.city:
            card['fields'].append({
                'label': '📍',
                'value': resort_obj.city
            })
        elif hasattr(resort_obj, 'country') and resort_obj.country:
            card['fields'].append({
                'label': '📍',
                'value': resort_obj.country.name
            })
        
        # Capacity
        if hasattr(resort_obj, 'capacity') and resort_obj.capacity:
            card['fields'].append({
                'label': '👥',
                'value': f"سعة: {resort_obj.capacity} شخص"
            })
        
        # Family friendly
        if hasattr(resort_obj, 'is_family_friendly') and resort_obj.is_family_friendly:
            card['fields'].append({
                'label': '👨‍👩‍👧‍👦',
                'value': 'عائلي'
            })
        
        # Price
        if hasattr(resort_obj, 'price_per_night') and resort_obj.price_per_night:
            card['fields'].append({
                'label': '💰',
                'value': f"{resort_obj.price_per_night:,} د.ع/ليلة"
            })
        
        # Match score
        card['fields'].append({
            'label': '⭐',
            'value': f"مطابقة: {score:.0%}"
        })
        
        # Actions
        card['actions'] = [
            {'label': '👁️ عرض المنتجع', 'action': 'view', 'url': url},
        ]
        
        return card
    
    def _render_job_card(self, job_obj, score: float, url: str) -> Dict:
        """Render job result card"""
        card = {
            'type': 'job',
            'emoji': '💼',
            'title': getattr(job_obj, 'title', 'وظيفة'),
            'url': url,
            'score': score,
            'fields': []
        }
        
        # Location
        if hasattr(job_obj, 'governorate') and job_obj.governorate:
            card['fields'].append({
                'label': '📍',
                'value': job_obj.governorate
            })
        elif hasattr(job_obj, 'city') and job_obj.city:
            card['fields'].append({
                'label': '📍',
                'value': job_obj.city
            })
        
        # Company
        if hasattr(job_obj, 'company_name') and job_obj.company_name:
            card['fields'].append({
                'label': '🏢',
                'value': job_obj.company_name
            })
        
        # Salary
        if hasattr(job_obj, 'salary_min') and job_obj.salary_min:
            card['fields'].append({
                'label': '💰',
                'value': f"من {job_obj.salary_min:,} د.ع"
            })
        
        # Job type
        if hasattr(job_obj, 'job_type') and job_obj.job_type:
            card['fields'].append({
                'label': '📋',
                'value': job_obj.job_type
            })
        
        # Match score
        card['fields'].append({
            'label': '⭐',
            'value': f"مطابقة: {score:.0%}"
        })
        
        # Actions
        card['actions'] = [
            {'label': '👁️ عرض الوظيفة', 'action': 'view', 'url': url},
        ]
        
        return card
    
    def _render_service_card(self, service_obj, score: float, url: str) -> Dict:
        """Render service result card"""
        card = {
            'type': 'service',
            'emoji': '🔧',
            'title': getattr(service_obj, 'title', 'خدمة'),
            'url': url,
            'score': score,
            'fields': []
        }
        
        # Location
        if hasattr(service_obj, 'governorate') and service_obj.governorate:
            card['fields'].append({
                'label': '📍',
                'value': service_obj.governorate
            })
        elif hasattr(service_obj, 'city') and service_obj.city:
            card['fields'].append({
                'label': '📍',
                'value': service_obj.city
            })
        
        # Service type
        if hasattr(service_obj, 'service_type') and service_obj.service_type:
            card['fields'].append({
                'label': '🔧',
                'value': service_obj.service_type
            })
        
        # Price
        if hasattr(service_obj, 'price') and service_obj.price:
            card['fields'].append({
                'label': '💰',
                'value': f"{service_obj.price:,} د.ع"
            })
        
        # Provider
        if hasattr(service_obj, 'service_provider') and service_obj.service_provider:
            card['fields'].append({
                'label': '👤',
                'value': service_obj.service_provider.name
            })
        
        # Match score
        card['fields'].append({
            'label': '⭐',
            'value': f"مطابقة: {score:.0%}"
        })
        
        # Actions
        card['actions'] = [
            {'label': '👁️ عرض الخدمة', 'action': 'view', 'url': url},
            {'label': '💬 تواصل', 'action': 'contact', 'url': url}
        ]
        
        return card
    
    def _render_auction_card(self, auction_obj, score: float, url: str) -> Dict:
        """Render auction result card"""
        card = {
            'type': 'auction',
            'emoji': '🔨',
            'title': 'مزاد عقاري',
            'url': url,
            'score': score,
            'fields': []
        }
        
        # Property info
        if hasattr(auction_obj, 'property') and auction_obj.property:
            card['title'] = f"مزاد: {auction_obj.property.display_title}"
            
            if hasattr(auction_obj.property, 'governorate') and auction_obj.property.governorate:
                card['fields'].append({
                    'label': '📍',
                    'value': auction_obj.property.governorate
                })
        
        # Starting price
        if hasattr(auction_obj, 'starting_price') and auction_obj.starting_price:
            card['fields'].append({
                'label': '💰',
                'value': f"السعر الابتدائي: {auction_obj.starting_price:,} د.ع"
            })
        
        # Status
        if hasattr(auction_obj, 'status') and auction_obj.status:
            status_map = {
                'active': 'نشط',
                'ended': 'منتهي',
                'upcoming': 'قادم'
            }
            card['fields'].append({
                'label': '⏰',
                'value': status_map.get(auction_obj.status, auction_obj.status)
            })
        
        # Match score
        card['fields'].append({
            'label': '⭐',
            'value': f"مطابقة: {score:.0%}"
        })
        
        # Actions
        card['actions'] = [
            {'label': '👁️ عرض المزاد', 'action': 'view', 'url': url},
        ]
        
        return card
    
    def _render_broker_card(self, broker_obj, score: float, url: str) -> Dict:
        """Render broker result card"""
        card = {
            'type': 'broker',
            'emoji': '👤',
            'title': getattr(broker_obj, 'name', 'دلال'),
            'url': url,
            'score': score,
            'fields': []
        }
        
        # Location
        if hasattr(broker_obj, 'governorate') and broker_obj.governorate:
            card['fields'].append({
                'label': '📍',
                'value': broker_obj.governorate
            })
        elif hasattr(broker_obj, 'city') and broker_obj.city:
            card['fields'].append({
                'label': '📍',
                'value': broker_obj.city
            })
        
        # Active properties
        if hasattr(broker_obj, 'active_properties_count'):
            active_count = broker_obj.active_properties_count()
            card['fields'].append({
                'label': '🏠',
                'value': f"{active_count} عقار نشط"
            })
        
        # Rating
        if hasattr(broker_obj, 'rating') and broker_obj.rating:
            stars = '⭐' * int(broker_obj.rating)
            card['fields'].append({
                'label': '⭐',
                'value': f"{stars} ({broker_obj.rating:.1f})"
            })
        
        # Match score
        card['fields'].append({
            'label': '⭐',
            'value': f"مطابقة: {score:.0%}"
        })
        
        # Actions
        card['actions'] = [
            {'label': '👁️ عرض الملف الشخصي', 'action': 'view', 'url': url},
            {'label': '💬 مراسلة', 'action': 'contact_broker', 'broker_id': broker_obj.id}
        ]
        
        return card
    
    def _render_generic_card(self, item: Any, score: float, url: str) -> Dict:
        """Render generic result card for unknown types"""
        card = {
            'type': 'generic',
            'emoji': '📄',
            'title': str(item),
            'url': url,
            'score': score,
            'fields': [
                {
                    'label': '⭐',
                    'value': f"مطابقة: {score:.0%}"
                }
            ],
            'actions': [
                {'label': '👁️ عرض', 'action': 'view', 'url': url}
            ]
        }
        
        return card
    
    def render_text_summary(self, results: List[Dict]) -> str:
        """Render results as text summary for chat interface"""
        if not results:
            return "لم يتم العثور على نتائج."
        
        lines = [f"وجدت {len(results)} نتيجة:\n"]
        
        for i, result in enumerate(results, 1):
            card = self._render_card(
                result['item'],
                result['type'],
                result['score'],
                result['url']
            )
            
            lines.append(f"{i}. {card['emoji']} {card['title']}")
            
            for field in card['fields']:
                lines.append(f"   {field['label']} {field['value']}")
            
            lines.append(f"   ⭐ مطابقة: {card['score']:.0%}")
            lines.append("")
        
        return '\n'.join(lines)


# Global instance
result_renderer = ResultRenderer()
