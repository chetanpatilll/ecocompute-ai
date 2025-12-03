import os
from datetime import datetime
from typing import Dict

import requests

class CarbonDataProvider:
    """Fetches real-time grid carbon intensity from multiple sources."""
    
    def __init__(self):
        self.electricity_maps_token = os.getenv("ELECTRICITY_MAPS_TOKEN", "demo")
        self.carbon_aware_url = "http://api.electricitymap.com"
        self.cache = {}
    
    def get_grid_carbon_intensity(self, region: str = "IN") -> Dict:
        """
        Fetch carbon intensity for a region.
        
        Args:
            region: ISO code (IN=India, US=USA, DE=Germany, etc.)
        
        Returns:
            {
                'carbonIntensity': float (gCO2/kWh),
                'timestamp': str,
                'greenness': 'LOW'|'MEDIUM'|'HIGH',
                'recommendation': str
            }
        """
        try:
            # Use ElectricityMaps API (free tier)
            url = f"https://api.electricitymap.com/v3/carbon-intensity/latest"
            params = {
                "countryCode": region,
                "auth-token": self.electricity_maps_token
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                carbon_intensity = data.get("carbonIntensity", 500)
                
                # Classify greenness (typical ranges)
                if carbon_intensity < 200:
                    greenness = "HIGH"
                    recommendation = "✅ Schedule jobs NOW - Clean grid"
                elif carbon_intensity < 400:
                    greenness = "MEDIUM"
                    recommendation = "⏳ Wait for better conditions"
                else:
                    greenness = "LOW"
                    recommendation = "❌ Defer jobs - Dirty grid"
                
                return {
                    'carbonIntensity': carbon_intensity,
                    'timestamp': datetime.now().isoformat(),
                    'greenness': greenness,
                    'recommendation': recommendation,
                    'region': region,
                    'unit': 'gCO2/kWh'
                }
            else:
                # Fallback mock data for demo
                return self._get_mock_data(region)
        
        except Exception as e:
            print(f"Error fetching carbon data: {e}")
            return self._get_mock_data(region)
    
    def _get_mock_data(self, region: str) -> Dict:
        """Return mock data for hackathon demo."""
        import random
        
        mock_data = {
            "IN": 800,    # India avg
            "US": 400,    # USA avg
            "DE": 350,    # Germany (renewable)
            "NO": 50,     # Norway (hydro)
            "AU": 600,    # Australia
        }
        
        intensity = mock_data.get(region, 500)
        # Add realistic variation
        intensity += random.randint(-100, 100)
        
        if intensity < 200:
            greenness = "HIGH"
            rec = "✅ Schedule jobs NOW"
        elif intensity < 400:
            greenness = "MEDIUM"
            rec = "⏳ Monitor grid"
        else:
            greenness = "LOW"
            rec = "❌ Defer jobs"
        
        return {
            'carbonIntensity': intensity,
            'timestamp': datetime.now().isoformat(),
            'greenness': greenness,
            'recommendation': rec,
            'region': region,
            'unit': 'gCO2/kWh',
            'is_mock': True
        }
    
    def get_multi_region_comparison(self, regions: list) -> Dict:
        """Compare carbon intensity across multiple regions."""
        comparison = {}
        for region in regions:
            comparison[region] = self.get_grid_carbon_intensity(region)

        # Find greenest region (lowest carbon intensity)
        greenest_region_code, greenest_data = min(
            comparison.items(),
            key=lambda item: item[1]['carbonIntensity']
        )

        return {
            'regions': comparison,
            'greenest_region': greenest_region_code,
            'greenest_intensity': greenest_data['carbonIntensity'],
            'timestamp': datetime.now().isoformat()
        }


# Export
carbon_provider = CarbonDataProvider()
