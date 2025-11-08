from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from .models import FoodDataset, DSDownloadRecord, DSViewRecord  # Importaciones relativas

class FoodTrendingService:
    
    @staticmethod
    def get_trending_food_datasets(timeframe='week', limit=5):
        """
        Obtiene datasets de comida trending basado en actividad reciente
        timeframe: 'week' o 'month'
        """
        if timeframe == 'week':
            since_date = datetime.utcnow() - timedelta(days=7)
        else:  # month
            since_date = datetime.utcnow() - timedelta(days=30)
        
        trending = db.session.query(
            FoodDataset,
            func.count(DSDownloadRecord.id).label('recent_downloads'),
            func.count(DSViewRecord.id).label('recent_views')
        ).select_from(FoodDataset).outerjoin(
            DSDownloadRecord, 
            db.and_(
                DSDownloadRecord.dataset_id == FoodDataset.id,
                DSDownloadRecord.download_date >= since_date
            )
        ).outerjoin(
            DSViewRecord,
            db.and_(
                DSViewRecord.dataset_id == FoodDataset.id,
                DSViewRecord.view_date >= since_date
            )
        ).filter(
            FoodDataset.kind == "food"
        ).group_by(
            FoodDataset.id
        ).order_by(
            func.count(DSDownloadRecord.id).desc(),
            func.count(DSViewRecord.id).desc()
        ).limit(limit).all()
        
        return [(dataset, downloads, views) for dataset, downloads, views in trending]

    @staticmethod
    def get_most_recipes_datasets(limit=5):
        """Ranking basado en número de recetas"""
        return FoodDataset.query.filter(
            FoodDataset.kind == "food",
            FoodDataset.total_recipes > 0
        ).order_by(
            FoodDataset.total_recipes.desc()
        ).limit(limit).all()

    @staticmethod
    def get_richest_ingredient_datasets(limit=5):
        """Datasets con mayor variedad de ingredientes"""
        return FoodDataset.query.filter(
            FoodDataset.kind == "food",
            FoodDataset.total_ingredients > 0
        ).order_by(
            FoodDataset.total_ingredients.desc()
        ).limit(limit).all()

    @staticmethod
    def get_popularity_ranking(limit=10, timeframe_days=7):
        """
        Ranking combinado usando un scoring system
        """
        since_date = datetime.utcnow() - timedelta(days=timeframe_days)
        
        # Subquery para descargas recientes
        downloads_subq = db.session.query(
            DSDownloadRecord.dataset_id,
            func.count(DSDownloadRecord.id).label('download_count')
        ).filter(
            DSDownloadRecord.download_date >= since_date
        ).group_by(
            DSDownloadRecord.dataset_id
        ).subquery()

        # Subquery para vistas recientes
        views_subq = db.session.query(
            DSViewRecord.dataset_id,
            func.count(DSViewRecord.id).label('view_count')
        ).filter(
            DSViewRecord.view_date >= since_date
        ).group_by(
            DSViewRecord.dataset_id
        ).subquery()

        ranking = db.session.query(
            FoodDataset,
            func.coalesce(downloads_subq.c.download_count, 0).label('downloads'),
            func.coalesce(views_subq.c.view_count, 0).label('views'),
            FoodDataset.total_recipes,
            (
                func.coalesce(downloads_subq.c.download_count, 0) * 3 +
                func.coalesce(views_subq.c.view_count, 0) * 1 +
                func.coalesce(FoodDataset.total_recipes, 0) * 2
            ).label('popularity_score')
        ).outerjoin(
            downloads_subq, downloads_subq.c.dataset_id == FoodDataset.id
        ).outerjoin(
            views_subq, views_subq.c.dataset_id == FoodDataset.id
        ).filter(
            FoodDataset.kind == "food"
        ).order_by(
            db.desc('popularity_score')
        ).limit(limit).all()

        return ranking

    @staticmethod
    def get_weekly_trending(limit=5):
        return FoodTrendingService.get_popularity_ranking(limit=limit, timeframe_days=7)

    @staticmethod
    def get_monthly_trending(limit=5):
        return FoodTrendingService.get_popularity_ranking(limit=limit, timeframe_days=30)

    @staticmethod
    def get_trending_for_homepage():
        """Método específico para la página principal"""
        return {
            'weekly_trending': FoodTrendingService.get_weekly_trending(limit=3),
            'most_recipes': FoodTrendingService.get_most_recipes_datasets(limit=3),
            'rich_ingredients': FoodTrendingService.get_richest_ingredient_datasets(limit=3)
        }