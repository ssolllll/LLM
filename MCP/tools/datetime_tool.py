from typing import Any
from datetime import datetime, timedelta, timezone
import calendar
import time


class DateTimeTool:
    """A datetime tool for handling date and time operations."""

    def __init__(self) -> None:
        self.name: str = "datetime"
        self.title: str = "Date & Time Manager"
        self.description: str = "Handles date and time operations including formatting, parsing, calculations, and timezone conversions"
        self.input_schema: dict[str, Any] = {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "current_time", "parse_datetime", "format_datetime", "add_time",
                        "subtract_time", "time_difference", "timezone_convert", "is_leap_year",
                        "days_in_month", "weekday", "timestamp_to_datetime", "datetime_to_timestamp",
                        "age_calculator", "business_days", "next_weekday", "previous_weekday"
                    ],
                    "description": "DateTime operation to perform"
                },
                "datetime_str": {
                    "type": "string",
                    "description": "DateTime string to parse or format (ISO format preferred)"
                },
                "format_str": {
                    "type": "string",
                    "description": "Format string for parsing/formatting (e.g., '%Y-%m-%d %H:%M:%S')"
                },
                "years": {
                    "type": "integer",
                    "default": 0,
                    "description": "Years to add/subtract"
                },
                "months": {
                    "type": "integer", 
                    "default": 0,
                    "description": "Months to add/subtract"
                },
                "days": {
                    "type": "integer",
                    "default": 0,
                    "description": "Days to add/subtract"
                },
                "hours": {
                    "type": "integer",
                    "default": 0,
                    "description": "Hours to add/subtract"
                },
                "minutes": {
                    "type": "integer",
                    "default": 0,
                    "description": "Minutes to add/subtract"
                },
                "seconds": {
                    "type": "integer",
                    "default": 0,
                    "description": "Seconds to add/subtract"
                },
                "from_timezone": {
                    "type": "string",
                    "description": "Source timezone (e.g., 'UTC', 'US/Eastern')"
                },
                "to_timezone": {
                    "type": "string",
                    "description": "Target timezone (e.g., 'UTC', 'US/Pacific')"
                },
                "datetime2_str": {
                    "type": "string",
                    "description": "Second datetime for comparison operations"
                },
                "year": {
                    "type": "integer",
                    "description": "Year for specific operations"
                },
                "month": {
                    "type": "integer",
                    "description": "Month for specific operations (1-12)"
                },
                "timestamp": {
                    "type": "number",
                    "description": "Unix timestamp"
                },
                "birth_date": {
                    "type": "string",
                    "description": "Birth date for age calculation (YYYY-MM-DD format)"
                },
                "target_weekday": {
                    "type": "integer",
                    "description": "Target weekday (0=Monday, 6=Sunday)"
                }
            },
            "required": ["operation"]
        }

    def format_for_llm(self) -> str:
        """Format tool information for LLM."""
        args_desc = []
        if "properties" in self.input_schema:
            for param_name, param_info in self.input_schema["properties"].items():
                arg_desc = f"- {param_name}: {param_info.get('description', 'No description')}"
                if param_name in self.input_schema.get("required", []):
                    arg_desc += " (required)"
                if "enum" in param_info:
                    arg_desc += f" (options: {', '.join(param_info['enum'])})"
                if "default" in param_info:
                    arg_desc += f" (default: {param_info['default']})"
                args_desc.append(arg_desc)

        output = f"Tool: {self.name}\n"
        if self.title:
            output += f"User-readable title: {self.title}\n"
        
        output += f"""Description: {self.description}
Arguments:
{chr(10).join(args_desc)}
"""
        return output

    def execute(self, operation: str, **kwargs) -> dict[str, Any]:
        """Execute the datetime operation."""
        try:
            if operation == "current_time":
                now = datetime.now()
                utc_now = datetime.now(timezone.utc)
                return {
                    "local_time": now.isoformat(),
                    "utc_time": utc_now.isoformat(),
                    "timestamp": now.timestamp(),
                    "formatted": now.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            elif operation == "parse_datetime":
                datetime_str = kwargs.get("datetime_str")
                format_str = kwargs.get("format_str")
                
                if not datetime_str:
                    return {"error": "datetime_str is required"}
                
                if format_str:
                    dt = datetime.strptime(datetime_str, format_str)
                else:
                    # Try common formats
                    formats = [
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%d",
                        "%d/%m/%Y",
                        "%m/%d/%Y",
                        "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%dT%H:%M:%SZ"
                    ]
                    dt = None
                    for fmt in formats:
                        try:
                            dt = datetime.strptime(datetime_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if dt is None:
                        return {"error": "Could not parse datetime string"}
                
                return {
                    "parsed_datetime": dt.isoformat(),
                    "year": dt.year,
                    "month": dt.month,
                    "day": dt.day,
                    "hour": dt.hour,
                    "minute": dt.minute,
                    "second": dt.second,
                    "weekday": dt.strftime("%A")
                }
            
            elif operation == "format_datetime":
                datetime_str = kwargs.get("datetime_str")
                format_str = kwargs.get("format_str", "%Y-%m-%d %H:%M:%S")
                
                if not datetime_str:
                    return {"error": "datetime_str is required"}
                
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                formatted = dt.strftime(format_str)
                
                return {"formatted": formatted, "original": datetime_str}
            
            elif operation in ["add_time", "subtract_time"]:
                datetime_str = kwargs.get("datetime_str")
                if not datetime_str:
                    return {"error": "datetime_str is required"}
                
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                
                delta = timedelta(
                    days=kwargs.get("days", 0),
                    hours=kwargs.get("hours", 0),
                    minutes=kwargs.get("minutes", 0),
                    seconds=kwargs.get("seconds", 0)
                )
                
                # Add months and years manually (approximate)
                months = kwargs.get("months", 0)
                years = kwargs.get("years", 0)
                
                if months or years:
                    new_month = dt.month + months + (years * 12)
                    new_year = dt.year + (new_month - 1) // 12
                    new_month = ((new_month - 1) % 12) + 1
                    
                    try:
                        dt = dt.replace(year=new_year, month=new_month)
                    except ValueError:
                        # Handle leap year edge cases
                        dt = dt.replace(year=new_year, month=new_month, day=28)
                
                if operation == "add_time":
                    result_dt = dt + delta
                else:
                    result_dt = dt - delta
                
                return {
                    "result": result_dt.isoformat(),
                    "original": datetime_str,
                    "operation": operation,
                    "delta_applied": {
                        "years": years,
                        "months": months,
                        "days": kwargs.get("days", 0),
                        "hours": kwargs.get("hours", 0),
                        "minutes": kwargs.get("minutes", 0),
                        "seconds": kwargs.get("seconds", 0)
                    }
                }
            
            elif operation == "time_difference":
                datetime_str = kwargs.get("datetime_str")
                datetime2_str = kwargs.get("datetime2_str")
                
                if not datetime_str or not datetime2_str:
                    return {"error": "Both datetime_str and datetime2_str are required"}
                
                dt1 = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                dt2 = datetime.fromisoformat(datetime2_str.replace('Z', '+00:00'))
                
                diff = dt2 - dt1
                
                return {
                    "difference_seconds": diff.total_seconds(),
                    "difference_days": diff.days,
                    "difference_hours": diff.total_seconds() / 3600,
                    "difference_minutes": diff.total_seconds() / 60,
                    "absolute_difference": abs(diff.total_seconds()),
                    "datetime1": datetime_str,
                    "datetime2": datetime2_str
                }
            
            elif operation == "timezone_convert":
                datetime_str = kwargs.get("datetime_str")
                from_tz = kwargs.get("from_timezone", "UTC")
                to_tz = kwargs.get("to_timezone", "UTC")
                
                if not datetime_str:
                    return {"error": "datetime_str is required"}
                
                # This is a simplified timezone conversion
                # In production, you'd want to use pytz or zoneinfo
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                
                return {
                    "converted": dt.isoformat(),
                    "original": datetime_str,
                    "from_timezone": from_tz,
                    "to_timezone": to_tz,
                    "note": "Timezone conversion requires proper timezone library (pytz/zoneinfo)"
                }
            
            elif operation == "is_leap_year":
                year = kwargs.get("year")
                if year is None:
                    year = datetime.now().year
                
                is_leap = calendar.isleap(year)
                return {"year": year, "is_leap_year": is_leap}
            
            elif operation == "days_in_month":
                year = kwargs.get("year", datetime.now().year)
                month = kwargs.get("month")
                
                if month is None:
                    return {"error": "month is required"}
                
                if not (1 <= month <= 12):
                    return {"error": "month must be between 1 and 12"}
                
                days = calendar.monthrange(year, month)[1]
                month_name = calendar.month_name[month]
                
                return {
                    "year": year,
                    "month": month,
                    "month_name": month_name,
                    "days_in_month": days
                }
            
            elif operation == "weekday":
                datetime_str = kwargs.get("datetime_str")
                if not datetime_str:
                    datetime_str = datetime.now().isoformat()
                
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                
                return {
                    "datetime": datetime_str,
                    "weekday_number": dt.weekday(),  # 0=Monday, 6=Sunday
                    "weekday_name": dt.strftime("%A"),
                    "is_weekend": dt.weekday() >= 5
                }
            
            elif operation == "timestamp_to_datetime":
                timestamp = kwargs.get("timestamp")
                if timestamp is None:
                    return {"error": "timestamp is required"}
                
                dt = datetime.fromtimestamp(timestamp)
                utc_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                
                return {
                    "timestamp": timestamp,
                    "local_datetime": dt.isoformat(),
                    "utc_datetime": utc_dt.isoformat(),
                    "formatted": dt.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            elif operation == "datetime_to_timestamp":
                datetime_str = kwargs.get("datetime_str")
                if not datetime_str:
                    return {"error": "datetime_str is required"}
                
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                timestamp = dt.timestamp()
                
                return {
                    "datetime": datetime_str,
                    "timestamp": timestamp,
                    "timestamp_ms": int(timestamp * 1000)
                }
            
            elif operation == "age_calculator":
                birth_date = kwargs.get("birth_date")
                if not birth_date:
                    return {"error": "birth_date is required"}
                
                birth_dt = datetime.strptime(birth_date, "%Y-%m-%d")
                now = datetime.now()
                
                age = now.year - birth_dt.year
                if now.month < birth_dt.month or (now.month == birth_dt.month and now.day < birth_dt.day):
                    age -= 1
                
                days_lived = (now - birth_dt).days
                next_birthday = birth_dt.replace(year=now.year + 1)
                if birth_dt.replace(year=now.year) > now:
                    next_birthday = birth_dt.replace(year=now.year)
                
                days_to_birthday = (next_birthday - now).days
                
                return {
                    "birth_date": birth_date,
                    "current_age": age,
                    "days_lived": days_lived,
                    "days_to_next_birthday": days_to_birthday,
                    "next_birthday": next_birthday.strftime("%Y-%m-%d")
                }
            
            elif operation == "business_days":
                datetime_str = kwargs.get("datetime_str")
                datetime2_str = kwargs.get("datetime2_str")
                
                if not datetime_str or not datetime2_str:
                    return {"error": "Both datetime_str and datetime2_str are required"}
                
                dt1 = datetime.fromisoformat(datetime_str.replace('Z', '+00:00')).date()
                dt2 = datetime.fromisoformat(datetime2_str.replace('Z', '+00:00')).date()
                
                if dt1 > dt2:
                    dt1, dt2 = dt2, dt1
                
                business_days = 0
                current_date = dt1
                
                while current_date <= dt2:
                    if current_date.weekday() < 5:  # Monday=0, Friday=4
                        business_days += 1
                    current_date += timedelta(days=1)
                
                return {
                    "start_date": dt1.isoformat(),
                    "end_date": dt2.isoformat(),
                    "business_days": business_days,
                    "total_days": (dt2 - dt1).days + 1
                }
            
            elif operation in ["next_weekday", "previous_weekday"]:
                datetime_str = kwargs.get("datetime_str", datetime.now().isoformat())
                target_weekday = kwargs.get("target_weekday")
                
                if target_weekday is None:
                    return {"error": "target_weekday is required (0=Monday, 6=Sunday)"}
                
                if not (0 <= target_weekday <= 6):
                    return {"error": "target_weekday must be between 0 and 6"}
                
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                current_weekday = dt.weekday()
                
                if operation == "next_weekday":
                    days_ahead = target_weekday - current_weekday
                    if days_ahead <= 0:
                        days_ahead += 7
                    result_dt = dt + timedelta(days=days_ahead)
                else:  # previous_weekday
                    days_behind = current_weekday - target_weekday
                    if days_behind <= 0:
                        days_behind += 7
                    result_dt = dt - timedelta(days=days_behind)
                
                weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                
                return {
                    "original_date": datetime_str,
                    "target_weekday": target_weekday,
                    "target_weekday_name": weekday_names[target_weekday],
                    "result_date": result_dt.isoformat(),
                    "days_difference": abs((result_dt - dt).days)
                }
            
            else:
                return {"error": f"Unknown operation: {operation}"}
        
        except Exception as e:
            return {"error": f"DateTime operation failed: {str(e)}"}