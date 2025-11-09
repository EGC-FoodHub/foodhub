class TrendingFormatter:
    
    @staticmethod
    def format_trending_item(item, metric_type='downloads'):
        """
        Formatea un item trending para visualización consistente
        """
        if isinstance(item, tuple):
            dataset = item[0]
            metric_value = item[1]
        else:
            dataset = item
            metric_value = getattr(item, f'recent_{metric_type}', 0)
        
        return {
            'id': dataset.id,
            'title': dataset.title,
            'main_author': dataset.main_author,
            'community': getattr(dataset, 'community', None),
            'metric_value': metric_value,
            'metric_type': metric_type,
            'total_recipes': getattr(dataset, 'total_recipes', 0),
            'total_ingredients': getattr(dataset, 'total_ingredients', 0),
            'url': f"/dataset/{dataset.id}/view"
        }

    @staticmethod
    def format_trending_list(trending_data, metric_type='downloads'):
        """
        Formatea una lista completa de datos trending
        """
        return [TrendingFormatter.format_trending_item(item, metric_type) 
                for item in trending_data]

    @staticmethod
    def format_for_homepage_display(trending_data):
        """
        Formatea específicamente para mostrar en homepage como en el ejemplo
        Ejemplo: "UVL Models for Automotive SPLs" – 250 downloads
        """
        display_text = []
        
        for i, item in enumerate(trending_data, 1):
            if isinstance(item, tuple):
                dataset, metric = item[0], item[1]
            else:
                dataset, metric = item, getattr(item, 'recent_downloads', 0)
            
            display_text.append(f'"{dataset.title}" – {metric} downloads')
        
        return display_text

    @staticmethod
    def format_api_response(trending_data, metric_type='downloads'):
        """
        Formatea para respuesta API consistente
        """
        formatted_data = TrendingFormatter.format_trending_list(trending_data, metric_type)
        
        return {
            'count': len(formatted_data),
            'metric_type': metric_type,
            'datasets': formatted_data
        }