"""
Instagram Service to call Instagram API
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any
import requests


class InstagramService:
    """
    Service for interacting with the Instagram Graph API
    """

    BASE_URL = "https://graph.instagram.com/v22.0"

    @staticmethod
    def get_user_media(
        ig_id: str,
        access_token: str,
    ) -> Dict[str, Any]:
        """
        Fetch a user's media from Instagram

        Args:
            ig_id: Instagram user ID
            access_token: Instagram user access token
            limit: Number of media items to fetch (default 25)

        Returns:
            Dict containing media data or error message
        """
        try:
            endpoint = f"{InstagramService.BASE_URL}/{ig_id}/media"
            params = {
                "access_token": access_token,
            }

            response = requests.get(endpoint, params=params, timeout=60)
            response.raise_for_status()  # 4XX/5XX responses

            return response.json()

        except requests.exceptions.RequestException as e:
            # Handle request errors
            return {"error": str(e)}

    @staticmethod
    def get_media_details(media_id: str, access_token: str) -> Dict[str, Any]:
        """
        Fetch details for a specific media item

        Args:
            media_id: Instagram media ID
            access_token: Instagram user access token

        Returns:
            Dict containing media details or error message
        """
        try:
            endpoint = f"{InstagramService.BASE_URL}/{media_id}"
            media_fields = [
                "id",
                "media_type",
                "media_url",
                "like_count",
                "permalink",
                "thumbnail_url",
                "timestamp",
                "username",
            ]
            children_fields = [
                "id",
                "media_type",
                "media_url",
                "thumbnail_url",
            ]
            media_fields = ",".join(media_fields)
            children_fields = ",".join(children_fields)
            params = {
                "access_token": access_token,
                "fields": media_fields + "," + "children"
                "{" + children_fields + "}",
            }

            response = requests.get(endpoint, params=params, timeout=60)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    @staticmethod
    def get_account_basic_insights(
        ig_id: str, access_token: str
    ) -> Dict[str, Any]:
        """
        Fetch basic account insights including follower count,
        engagement rate, etc.

        Args:
            ig_id: Instagram user ID
            access_token: Instagram user access token

        Returns:
            Dict containing basic account insights or error message
        """
        try:
            # Get follower count and other metrics
            field_values = [
                "accounts_engaged",
                "follower_count",
                "online_followers",
                "reach",
                "total_interactions",
                "likes",
                "comments",
                "shares",
                "saves",
            ]
            metrics = ",".join(field_values)
            endpoint = f"{InstagramService.BASE_URL}/{ig_id}/insights"
            params = {
                "metric": metrics,
                "period": "day",
                "metric_type": "total_value",
                "access_token": access_token,
            }

            response = requests.get(endpoint, params=params, timeout=60)
            response.raise_for_status()
            insights_data = response.json()

            # Get user media to calculate average likes
            media_response = InstagramService.get_user_media(
                ig_id, access_token
            )
            media_ids = [
                item["id"] for item in media_response.get("data", [])
            ][
                :10
            ]  # Get recent 10 posts

            # Calculate engagement metrics
            total_likes = 0
            total_comments = 0
            total_saves = 0
            total_shares = 0

            for media_id in media_ids:
                media_details = InstagramService.get_media_details(
                    media_id, access_token
                )
                total_likes += media_details.get("like_count", 0)

                # Get media insights
                media_insights = InstagramService.get_media_insights(
                    media_id, access_token
                )
                total_comments += media_insights.get("comments", {}).get(
                    "value", 0
                )
                total_saves += media_insights.get("saved", {}).get("value", 0)
                total_shares += media_insights.get("shares", {}).get(
                    "value", 0
                )

            avg_likes = total_likes / len(media_ids) if media_ids else 0
            avg_comments = total_comments / len(media_ids) if media_ids else 0
            avg_saves = total_saves / len(media_ids) if media_ids else 0
            avg_shares = total_shares / len(media_ids) if media_ids else 0

            # Calculate engagement rate
            # (likes + comments + saves + shares) / followers * 100
            follower_count = 0
            for metric in insights_data.get("data", []):
                if metric["name"] == "follower_count":
                    follower_count = metric["total_value"]["value"]
                    break

            engagement_rate = (
                (
                    (avg_likes + avg_comments + avg_saves + avg_shares)
                    / follower_count
                    * 100
                )
                if follower_count
                else 0
            )

            return {
                "follower_count": follower_count,
                "avg_likes": avg_likes,
                "avg_comments": avg_comments,
                "avg_saves": avg_saves,
                "avg_shares": avg_shares,
                "engagement_rate": engagement_rate,
                "raw_insights": insights_data,
            }

        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    @staticmethod
    def get_engaged_audience_demographics(
        ig_id: str,
        access_token: str,
        timeframe: str,
    ) -> Dict[str, Any]:
        """
        Fetch engaged audience demographics

            Args:
                ig_id: Instagram user ID
                access_token: Instagram user access token
        """
        # Get follower count and other metrics
        endpoint = f"{InstagramService.BASE_URL}/{ig_id}/insights"
        metrics = ["engaged_audience_demographics"]
        params = {
            "metric": ",".join(metrics),
            "period": "lifetime",
            "timeframe": timeframe,
            "metric_type": "total_value",
            "access_token": access_token,
        }

        response = requests.get(endpoint, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        return data

    @staticmethod
    def get_follows_and_unfollows(
        ig_id: str,
        access_token: str,
    ) -> Dict[str, Any]:
        """
        Fetch engaged audience demographics

            Args:
                ig_id: Instagram user ID
                access_token: Instagram user access token
        """
        # Get follower count and other metrics
        endpoint = f"{InstagramService.BASE_URL}/{ig_id}/insights"
        metrics = ["follows_and_unfollows"]
        params = {
            "metric": ",".join(metrics),
            "period": "day",
            "breakdown": "follow_type",
            "metric_type": "total_value",
            "access_token": access_token,
        }

        response = requests.get(endpoint, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        return data

    @staticmethod
    def get_follower_demographics(
        ig_id: str,
        access_token: str,
        timeframe: str,
        breakdown: str,
    ) -> Dict[str, Any]:
        """
        Follower demographics
        breakdown: age, country, city, gender
        timeframe: this_month, this_week

            Args:
                ig_id: Instagram user ID
                access_token: Instagram user access token
        """
        # Get follower count and other metrics
        endpoint = f"{InstagramService.BASE_URL}/{ig_id}/insights"
        metrics = ["follower_demographics"]
        params = {
            "metric": ",".join(metrics),
            "period": "lifetime",
            "metric_type": "total_value",
            "timeframe": timeframe,
            "breakdown": breakdown,
            "access_token": access_token,
        }

        response = requests.get(endpoint, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        return data

    @staticmethod
    def get_media_insights(media_id: str, access_token: str) -> Dict[str, Any]:
        """
        Fetch insights for a specific media item

        Args:
            media_id: Instagram media ID
            access_token: Instagram user access token

        Returns:
            Dict containing media insights or error message
        """
        try:
            endpoint = f"{InstagramService.BASE_URL}/{media_id}/insights"
            params = {
                "metric": "likes,comments,shares,saved,impressions,reach",
                "access_token": access_token,
            }

            response = requests.get(endpoint, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            # Format data into a more usable structure
            formatted_data = {}
            for metric in data.get("data", []):
                metric_name = metric["name"]
                metric_value = (
                    metric["values"][0]["value"] if metric.get("values") else 0
                )
                formatted_data[metric_name] = {
                    "value": metric_value,
                    "title": metric.get("title", ""),
                    "description": metric.get("description", ""),
                }

            return formatted_data

        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    @staticmethod
    def get_followers_growth(
        ig_id: str, access_token: str, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get follower growth data for the last specified number of days

        Args:
            ig_id: Instagram user ID
            access_token: Instagram user access token
            days: Number of days to look back (default 30)

        Returns:
            Dict containing follower growth data or error message
        """
        try:
            current_time = int(time.time())
            past_time = int(
                (datetime.now() - timedelta(days=days)).timestamp()
            )

            endpoint = f"{InstagramService.BASE_URL}/{ig_id}/insights"
            params = {
                "metric": "follower_count",
                "period": "day",
                "metric_type": "time_series",
                "since": past_time,
                "until": current_time,
                "access_token": access_token,
            }

            response = requests.get(endpoint, params=params, timeout=60)
            response.raise_for_status()

            data = response.json()
            formatted_data = []

            if "data" in data and data["data"]:
                for metric in data["data"]:
                    if metric["name"] == "follower_count":
                        for value in metric.get("values", []):
                            formatted_data.append(
                                {
                                    "date": value.get("end_time", ""),
                                    "value": value.get("value", 0),
                                }
                            )

            return {"follower_growth": formatted_data}

        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    @staticmethod
    def get_post_engagements(
        ig_id: str, access_token: str, months: int = 6
    ) -> Dict[str, Any]:
        """
        Get engagement data for posts from the last specified number of months

        Args:
            ig_id: Instagram user ID
            access_token: Instagram user access token
            months: Number of months to look back (default 6)

        Returns:
            Dict containing post engagement data or error message
        """
        try:
            # Get media from the last few months
            endpoint = f"{InstagramService.BASE_URL}/{ig_id}/media"
            params = {
                "access_token": access_token,
                "fields": "id,timestamp",
                "limit": 50,  # Get a reasonable number to analyze
            }

            response = requests.get(endpoint, params=params, timeout=60)
            response.raise_for_status()

            cutoff_date = datetime.now() - timedelta(days=30 * months)
            media_data = response.json().get("data", [])

            monthly_data = {}
            for month_idx in range(months):
                month = (
                    datetime.now() - timedelta(days=30 * month_idx)
                ).strftime("%Y-%m")
                monthly_data[month] = {"count": 0, "total_engagement": 0}

            for media in media_data:
                media_date = datetime.strptime(
                    media["timestamp"], "%Y-%m-%dT%H:%M:%S%z"
                )
                if media_date.replace(tzinfo=None) < cutoff_date:
                    continue

                month_key = media_date.strftime("%Y-%m")
                if month_key not in monthly_data:
                    continue

                # Get engagement metrics for this post
                insights = InstagramService.get_media_insights(
                    media["id"], access_token
                )
                engagement = (
                    insights.get("likes", {}).get("value", 0)
                    + insights.get("comments", {}).get("value", 0)
                    + insights.get("shares", {}).get("value", 0)
                    + insights.get("saved", {}).get("value", 0)
                )

                monthly_data[month_key]["count"] += 1
                monthly_data[month_key]["total_engagement"] += engagement

            # Calculate the average engagement per post per month
            result = []
            for month, data in monthly_data.items():
                avg_engagement = (
                    data["total_engagement"] / data["count"]
                    if data["count"] > 0
                    else 0
                )
                result.append(
                    {
                        "month": month,
                        "average_engagement": avg_engagement,
                        "post_count": data["count"],
                    }
                )

            return {
                "post_engagements_by_month": sorted(
                    result, key=lambda x: x["month"]
                )
            }

        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    @staticmethod
    def get_current_month_likes(
        ig_id: str, access_token: str
    ) -> Dict[str, Any]:
        """
        Get likes data for the current month by day

        Args:
            ig_id: Instagram user ID
            access_token: Instagram user access token

        Returns:
            Dict containing likes data for current month or error message
        """
        try:
            # Get start and end time for the current month
            now = datetime.now()
            start_of_month = datetime(now.year, now.month, 1)
            start_timestamp = int(start_of_month.timestamp())
            current_timestamp = int(now.timestamp())

            endpoint = f"{InstagramService.BASE_URL}/{ig_id}/insights"
            params = {
                "metric": "likes",
                "period": "day",
                "metric_type": "time_series",
                "since": start_timestamp,
                "until": current_timestamp,
                "access_token": access_token,
            }

            response = requests.get(endpoint, params=params, timeout=60)
            response.raise_for_status()

            data = response.json()
            likes_data = []

            if "data" in data and data["data"]:
                for metric in data["data"]:
                    if metric["name"] == "likes":
                        for value in metric.get("values", []):
                            likes_data.append(
                                {
                                    "date": value.get("end_time", ""),
                                    "value": value.get("value", 0),
                                }
                            )

            return {"current_month_likes": likes_data}

        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    @staticmethod
    def get_demographic_insights(
        ig_id: str, access_token: str
    ) -> Dict[str, Any]:
        """
        Get demographic insights including location
        by country, city, gender, and age

        Args:
            ig_id: Instagram user ID
            access_token: Instagram user access token

        Returns:
            Dict containing demographic insights or error message
        """
        try:
            endpoint = f"{InstagramService.BASE_URL}/{ig_id}/insights"
            params = {
                "metric": "follower_demographics",
                "period": "lifetime",
                "timeframe": "this_month",
                "breakdown": "country,city,gender,age",
                "metric_type": "total_value",
                "access_token": access_token,
            }

            response = requests.get(endpoint, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            # Process demographic data
            countries = []
            cities = []
            gender_data = []
            age_gender_data = []

            if "data" in data:
                for metric in data["data"]:
                    if metric["name"] == "follower_demographics":
                        breakdowns = metric.get("total_value", {}).get(
                            "breakdowns", []
                        )

                        for breakdown in breakdowns:
                            dimension_keys = breakdown.get(
                                "dimension_keys", []
                            )

                            # Process country data
                            if "country" in dimension_keys:
                                countries = []
                                for result in breakdown.get("results", []):
                                    country_idx = dimension_keys.index(
                                        "country"
                                    )
                                    country = result["dimension_values"][
                                        country_idx
                                    ]
                                    countries.append(
                                        {
                                            "country": country,
                                            "value": result["value"],
                                        }
                                    )

                            # Process city data
                            if "city" in dimension_keys:
                                cities = []
                                for result in breakdown.get("results", []):
                                    city_idx = dimension_keys.index("city")
                                    city = result["dimension_values"][city_idx]
                                    cities.append(
                                        {
                                            "city": city,
                                            "value": result["value"],
                                        }
                                    )

                            # Process gender data
                            if (
                                "gender" in dimension_keys
                                and "age" not in dimension_keys
                            ):
                                gender_data = []
                                for result in breakdown.get("results", []):
                                    gender_idx = dimension_keys.index("gender")
                                    gender = result["dimension_values"][
                                        gender_idx
                                    ]
                                    gender_data.append(
                                        {
                                            "gender": gender,
                                            "value": result["value"],
                                        }
                                    )

                            # Process age and gender data
                            if (
                                "gender" in dimension_keys
                                and "age" in dimension_keys
                            ):
                                age_gender_data = []
                                for result in breakdown.get("results", []):
                                    gender_idx = dimension_keys.index("gender")
                                    age_idx = dimension_keys.index("age")
                                    gender = result["dimension_values"][
                                        gender_idx
                                    ]
                                    age = result["dimension_values"][age_idx]
                                    age_gender_data.append(
                                        {
                                            "gender": gender,
                                            "age": age,
                                            "value": result["value"],
                                        }
                                    )

            return {
                "countries": countries,
                "cities": cities,
                "gender_split": gender_data,
                "age_gender_split": age_gender_data,
            }

        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
