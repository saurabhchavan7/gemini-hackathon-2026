# backend/services/clustering_service.py - SIMPLE VERSION

from typing import List, Dict
import google.generativeai as genai
from core.config import settings

class ClusteringService:
    """
    AI-Powered Theme Clustering Service - Domain-based with AI naming
    """
    
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("[CLUSTERING_SERVICE] Initialized")
    
    def generate_clusters(
        self,
        memories: List[Dict],
        num_clusters: int = 4
    ) -> List[Dict]:
        """
        Generate theme clusters by grouping domains and using AI to name them
        """
        
        print(f"[CLUSTERING] Analyzing {len(memories)} memories...")
        
        # Group by domain
        domain_groups = {}
        for memory in memories:
            domain = memory.get('domain', 'unknown')
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(memory)
        
        print(f"[CLUSTERING] Found {len(domain_groups)} domain groups")
        
        # Use Gemini to name each domain cluster
        clusters = []
        colors = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444", "#06B6D4"]
        
        for idx, (domain, mems) in enumerate(domain_groups.items()):
            # Get AI-generated name for this domain cluster
            cluster_info = self._generate_cluster_name(mems[:5])
            
            clusters.append({
                "id": f"domain_{domain}",
                "name": cluster_info['name'],
                "description": cluster_info['description'],
                "captureIds": [m['id'] for m in mems],
                "createdAt": max(m.get('created_at', '') for m in mems) if mems else '',
                "updatedAt": max(m.get('created_at', '') for m in mems) if mems else '',
                "color": colors[idx % len(colors)]
            })
        
        print(f"[CLUSTERING] Generated {len(clusters)} theme clusters")
        return clusters
    
    def _generate_cluster_name(self, memories: List[Dict]) -> Dict[str, str]:
        """
        Use Gemini to generate a creative name and description
        """
        
        # Build context
        context = "Memories in this cluster:\n\n"
        for i, memory in enumerate(memories[:5], 1):
            context += f"{i}. Title: {memory.get('title', 'Untitled')}\n"
            context += f"   Summary: {memory.get('one_line_summary', 'No summary')}\n"
            context += f"   Domain: {memory.get('domain', 'unknown')}\n"
            context += f"   Tags: {', '.join(memory.get('tags', []))}\n\n"
        
        prompt = f"""Analyze these related items and create a catchy theme name.

{context}

Respond in this EXACT format:
NAME: [2-4 word creative theme name]
DESCRIPTION: [One sentence describing what connects these items]

Examples:
NAME: Career Growth Path
DESCRIPTION: Job applications, skills learning, and professional development

NAME: Tech Stack Research  
DESCRIPTION: Frontend frameworks, programming languages, and development tools

NAME: Financial Planning
DESCRIPTION: Bills, payments, subscriptions, and money management

Your response:"""
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Parse response
            lines = text.split('\n')
            name = "Untitled Cluster"
            description = "Related items"
            
            for line in lines:
                if line.startswith('NAME:'):
                    name = line.replace('NAME:', '').strip()
                elif line.startswith('DESCRIPTION:'):
                    description = line.replace('DESCRIPTION:', '').strip()
            
            print(f"[CLUSTERING] Generated cluster: {name}")
            
            return {
                "name": name,
                "description": description
            }
            
        except Exception as e:
            print(f"[CLUSTERING] Failed to generate cluster name: {e}")
            domain = memories[0].get('domain', 'unknown')
            return {
                "name": domain.replace('_', ' ').title(),
                "description": f"Items related to {domain}"
            }