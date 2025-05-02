import requests
import json
from typing import List, Dict, Any, Optional
from app.core.config import settings

class SearchService:
    """
    Service for performing web searches using the Exa API.
    """
    def __init__(self):
        """Initialize the search service with Exa API configuration."""
        self.api_key = settings.EXA_API_KEY
        self.base_url = settings.EXA_BASE_URL
        
    def search_web(
        self, 
        query: str, 
        content_filter: str = "medium", 
        educational_focus: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search the web using Exa AI's search API with content filtering.
        
        Args:
            query: The search query string
            content_filter: Level of content filtering ("none", "low", "medium", "high")
            educational_focus: Whether to prioritize educational domains
            
        Returns:
            List of search result dictionaries
        """
        if not self.api_key:
            print("No EXA_API_KEY found in environment variables")
            return []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "type": "neural",  # Use neural search for faster results
            "numResults": 10,  # Increase results to get more image options
            "safeSearch": content_filter,  # Apply content filtering
            "contents": {
                "text": True,
                "highlights": True,
                "summary": True,
                "image": True,  # Keep image content
                "livecrawl": "fallback",  # Only use livecrawl as fallback
                "livecrawlTimeout": 3000  # Reduce timeout to 3 seconds
            }
        }
        
        # If educational focus is requested, modify the query
        if educational_focus:
            payload["useAuthorityFilter"] = True
            
            # Check if the query is about a non-educational topic
            educational_keywords = [
                'math', 'science', 'history', 'geography', 'literature', 
                'physics', 'chemistry', 'biology', 'economics', 'politics', 
                'grammar', 'algebra', 'geometry', 'calculus', 'astronomy'
            ]
            is_educational_query = any(keyword in query.lower() for keyword in educational_keywords)
            
            # For non-educational topics, add educational framing
            if not is_educational_query:
                payload["query"] = f"{payload['query']} educational perspective learning material"

        try:
            print(f"Making Exa API request for query: {query}")
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=10  # Use a 10-second timeout for reliability
            )
            
            print(f"Exa API response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                
                # Filter out low-quality results
                results = data.get("results", [])
                filtered_results = []
                for result in results:
                    if result.get("score", 0) > 0.3 and result.get("text") and result.get("url"):
                        # Calculate relevance score for better image selection
                        relevance_score = result.get("score", 0)
                        
                        # Boost score for educational domains
                        url = result.get('url', '')
                        if any(domain in url for domain in ['edu', 'org', 'gov', 'school', 'learn', 'teach']):
                            relevance_score += 0.2
                        
                        # Boost score for results with good images
                        if result.get('image') and isinstance(result.get('image'), str):
                            # Check if image URL contains educational keywords
                            image_url = result.get('image')
                            if any(keyword in image_url.lower() for keyword in ['school', 'class', 'education', 'learn']):
                                relevance_score += 0.1
                        
                        # Store the calculated relevance score
                        result['relevance_score'] = relevance_score
                        filtered_results.append(result)
                
                # Sort results by relevance score
                filtered_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
                
                # Return up to 5 filtered results
                return filtered_results[:5]
            else:
                print(f"Exa API error: {response.text}")
                return []
            
        except requests.exceptions.Timeout:
            print("Exa API request timed out")
            return []
        except requests.exceptions.RequestException as e:
            print(f"Error making Exa API request: {e}")
            return []
            
    def format_web_results(self, results: List[Dict[str, Any]], topic: str = "") -> Dict[str, Any]:
        """
        Format web search results into a readable string with categorized links and extract image URL.
        
        Args:
            results: List of search result dictionaries
            topic: The current topic (for relevance scoring)
            
        Returns:
            Dictionary with formatted_text and image_url
        """
        topic_lower = topic.lower() if topic else ""
        
        if not results:
            return {
                "formatted_text": "No additional web resources found.",
                "image_url": None
            }

        # Categorize results by domain type
        categories = {
            "YouTube": [],
            "Twitter/X": [],
            "Wikipedia": [],
            "News": [],
            "Educational": [],
            "Other": []
        }

        # Show exactly 5 results total
        total_count = 0
        for result in results[:10]:  # Look at top 10 results
            if total_count >= 5:
                break
            
            url = result.get('url', '')
            domain = url.split('/')[2] if '/' in url else url
            
            # Categorize based on domain
            if 'youtube.com' in domain or 'youtu.be' in domain:
                if len(categories["YouTube"]) < 1:  # Limit to 1 YouTube video
                    categories["YouTube"].append(result)
                    total_count += 1
            elif 'twitter.com' in domain or 'x.com' in domain:
                if len(categories["Twitter/X"]) < 1:  # Limit to 1 Twitter/X post
                    categories["Twitter/X"].append(result)
                    total_count += 1
            elif 'wikipedia.org' in domain:
                if len(categories["Wikipedia"]) < 1:  # Limit to 1 Wikipedia article
                    categories["Wikipedia"].append(result)
                    total_count += 1
            elif any(site in domain for site in ['news', 'times', 'post', 'journal', 'reuters', 'bbc', 'cnn']):
                if len(categories["News"]) < 1:  # Limit to 1 news article
                    categories["News"].append(result)
                    total_count += 1
            elif any(site in domain for site in ['edu', 'org', 'gov']):
                if len(categories["Educational"]) < 1:  # Limit to 1 educational resource
                    categories["Educational"].append(result)
                    total_count += 1
            else:
                if len(categories["Other"]) < 1:  # Limit to 1 other resource
                    categories["Other"].append(result)
                    total_count += 1

        # Find an image URL from the results
        image_url = self._find_best_image(results, topic_lower)

        formatted_results = []
        
        # Add results by category
        for category, cat_results in categories.items():
            if cat_results:
                formatted_results.append(f"\n{category} Resources:")
                for result in cat_results:
                    formatted_results.append(self._format_web_resource(result))

        if not formatted_results:  # If no results found
            formatted_text = "No additional web resources found."
        else:
            formatted_text = "\n".join(formatted_results[:5])  # Limit to 5 lines

        return {
            "formatted_text": formatted_text,
            "image_url": image_url
        }
        
    def _find_best_image(self, results: List[Dict[str, Any]], topic_lower: str = "") -> Optional[str]:
        """
        Find the best image URL from search results.
        
        Args:
            results: List of search result dictionaries
            topic_lower: Lowercase topic string for relevance scoring
            
        Returns:
            Best image URL or None if no suitable image found
        """
        # First, analyze and score all results with images
        scored_results = []
        for r in results:
            # Only consider results with images
            has_image = bool(r.get('image') or r.get('thumbnail') or r.get('imageUrl') or r.get('favicon'))
            if not has_image:
                continue
                
            url = r.get('url', '').lower()
            title = r.get('title', '').lower()
            text = r.get('text', '').lower()
            summary = r.get('summary', '').lower()
            
            # Initialize comprehensive scoring system
            image_score = r.get('relevance_score', 0) * 10  # Base score from API relevance
            
            # 1. Domain authority scoring
            domain_score = 0
            if any(domain in url for domain in ['wikipedia', 'news', 'bbc', 'cnn', 'reuters']):
                domain_score = 1  # Slightly prefer well-known sources
            image_score += domain_score * 2
            
            # 2. Content relevance scoring
            content_score = 0
            if topic_lower and topic_lower in title:
                content_score += 2
            if topic_lower and topic_lower in summary:
                content_score += 1
            image_score += content_score * 2
            
            # 3. Image quality heuristics
            image_url_to_check = r.get('image') or r.get('thumbnail') or r.get('imageUrl') or ''
            if isinstance(image_url_to_check, str):
                if any(term in image_url_to_check.lower() for term in ['diagram', 'illustration', 'figure', 'chart']):
                    image_score += 1
            
            # Store the final score
            r['image_score'] = image_score
            scored_results.append(r)
        
        # Sort by comprehensive image score (higher is better)
        scored_results.sort(key=lambda x: x.get('image_score', 0), reverse=True)
        
        # First pass: Try to find high-quality images (non-favicon)
        for result in scored_results:
            # Check if the result has an image URL in various fields and formats
            if isinstance(result.get('image'), str) and result.get('image').startswith(('http://', 'https://')):
                # Verify the image URL doesn't contain terms that suggest it's an icon or logo
                image_lower = result.get('image').lower()
                if not any(term in image_lower for term in ['icon', 'logo', 'favicon', 'avatar', 'button']):
                    return result['image']
            elif result.get('thumbnail') and isinstance(result.get('thumbnail'), str) and result.get('thumbnail').startswith(('http://', 'https://')):
                # Verify the thumbnail URL doesn't contain terms that suggest it's an icon or logo
                thumb_lower = result.get('thumbnail').lower()
                if not any(term in thumb_lower for term in ['icon', 'logo', 'favicon', 'avatar', 'button']):
                    return result['thumbnail']
            elif result.get('imageUrl') and isinstance(result.get('imageUrl'), str) and result.get('imageUrl').startswith(('http://', 'https://')):
                # Verify the imageUrl doesn't contain terms that suggest it's an icon or logo
                img_url_lower = result.get('imageUrl').lower()
                if not any(term in img_url_lower for term in ['icon', 'logo', 'favicon', 'avatar', 'button']):
                    return result['imageUrl']
                    
        # Second pass: If no high-quality images found, accept any image including favicons
        for result in scored_results:
            if isinstance(result.get('image'), str) and result.get('image').startswith(('http://', 'https://')):
                return result['image']
            elif result.get('thumbnail') and isinstance(result.get('thumbnail'), str) and result.get('thumbnail').startswith(('http://', 'https://')):
                return result['thumbnail']
            elif result.get('imageUrl') and isinstance(result.get('imageUrl'), str) and result.get('imageUrl').startswith(('http://', 'https://')):
                return result['imageUrl']
            elif isinstance(result.get('image'), bool) and result.get('favicon') and isinstance(result.get('favicon'), str) and result.get('favicon').startswith(('http://', 'https://')):
                # Only use favicon as a last resort
                return result['favicon']
                
        return None
        
    def _format_web_resource(self, result: Dict[str, Any]) -> str:
        """
        Format a single web resource with its type.
        
        Args:
            result: Search result dictionary
            
        Returns:
            Formatted string with resource information
        """
        url = result.get('url', '')
        domain = url.split('/')[2] if '/' in url else url

        # General-purpose resource type labeling
        if 'youtube.com' in domain or 'youtu.be' in domain:
            resource_type = "YouTube Video"
        elif 'twitter.com' in domain or 'x.com' in domain:
            resource_type = "Twitter/X Post"
        elif 'wikipedia.org' in domain:
            resource_type = "Wikipedia Article"
        elif any(site in domain for site in ['news', 'times', 'post', 'journal', 'reuters', 'bbc', 'cnn']):
            resource_type = "News Article"
        else:
            resource_type = "Web Resource"

        title = result.get('title', 'No title')
        summary = result.get('summary', '')
        highlights = result.get('highlights', [])

        formatted = [f"- [{title}]({url}) - {resource_type}"]
        if summary:
            formatted.append(f"  - Summary: {summary[:50]}...")
        if highlights:
            formatted.append("  - Highlights:")
            for highlight in highlights[:2]:
                formatted.append(f"    - {highlight[:50]}...")
        return "\n".join(formatted)
