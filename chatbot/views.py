from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from textwrap import dedent
from django.db.models.functions import Sqrt, Power
from django.db.models import F, ExpressionWrapper, FloatField
import json
import requests

from .models import Dish, Restaurant

# Kiểm tra xem GOOGLE_API_KEY đã được thiết lập chưa
if not settings.GOOGLE_API_KEY:
    print("Lỗi: Biến môi trường GOOGLE_API_KEY chưa được thiết lập trong settings.py")
    # Có thể trả về một thông báo lỗi cụ thể cho người dùng nếu cần
    GENAI_AVAILABLE = False
else:
    import google.generativeai as genai
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        GENAI_AVAILABLE = True
    except Exception as e:
        print(f"Lỗi khi khởi tạo mô hình Gemini: {e}")
        GENAI_AVAILABLE = False


def chatbot_view(request):
    return render(request, 'chatbot/chatbot.html')

def get_chatbot_response(request):
    if request.method == 'POST':
        user_input = request.POST.get('user_input', '')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if latitude and longitude and "nhà hàng gần đây" in user_input.lower():
            response = find_nearby_restaurants_google(latitude, longitude)
        elif "nhà hàng gần đây" in user_input.lower() and not latitude and not longitude:
            response = "Để tìm nhà hàng gần bạn, vui lòng cho phép tôi truy cập vị trí của bạn hoặc cho biết khu vực bạn quan tâm."
        else:
            response = generate_chatbot_response_logic(user_input)

        return JsonResponse({'response': response})
    return JsonResponse({'error': 'Invalid request'})

def generate_chatbot_response_logic(user_input):
    user_input_lower = user_input.lower()

    if "xin chào" in user_input_lower or "hello" in user_input_lower:
        return "Chào bạn! Bạn đang thèm đồ Hàn Quốc hả? Tuyệt vời! Bạn muốn tìm hiểu về món ăn, công thức hay nhà hàng nào gần đây?"
    elif ("món ăn" in user_input_lower and "liệt kê" in user_input_lower) or "gợi ý món ăn" in user_input_lower:
        dishes = Dish.objects.all().order_by('?')[:3]
        if dishes:
            dish_list = "\n".join([f"- **{dish.name}**: {dish.description[:50]}..." for dish in dishes])
            return f"""Đây là một vài gợi ý món ăn Hàn Quốc có thể bạn sẽ thích:\n{dish_list}\n\nBạn có muốn biết thêm chi tiết về món nào không?"""
        else:
            return "Rất tiếc, hiện tại không có món ăn nào trong cơ sở dữ liệu."
    elif "mô tả" in user_input_lower:
        parts = user_input_lower.split("mô tả", 1)
        if len(parts) > 1:
            dish_name = parts[1].strip()
            try:
                dish = Dish.objects.get(name__iexact=dish_name)
                return f"**{dish.name}**\n\n{dish.description}\n\nNguyên liệu chính có thể bao gồm: {dish.ingredients}.\n\nBạn có muốn biết thêm về nguồn gốc, cách làm hoặc các biến thể của món ăn này không?"
            except Dish.DoesNotExist:
                return f"Rất tiếc, tôi chưa có thông tin chi tiết về món '{dish_name}'. Bạn có muốn thử tìm kiếm món khác không?"
            else:
                return "Bạn muốn tôi mô tả món ăn nào vậy?"
    elif "nhà hàng gần đây" in user_input_lower:
        return "Để tìm nhà hàng gần bạn, vui lòng cho phép tôi truy cập vị trí của bạn hoặc cho biết khu vực bạn quan tâm."
    else:
        if GENAI_AVAILABLE and 'model' in globals():
            prompt = f"""Bạn là một trợ lý chuyên về ẩm thực Hàn Quốc và nhà hàng.
            Nếu người dùng hỏi một câu hỏi liên quan đến ẩm thực Hàn Quốc (ví dụ: món ăn, công thức, nguyên liệu, lịch sử món ăn) hoặc nhà hàng (ví dụ: địa điểm, menu, đặt bàn, đánh giá), hãy trả lời một cách hữu ích, thú vị và sử dụng markdown nếu cần.
            Nếu câu hỏi không liên quan đến ẩm thực Hàn Quốc hoặc nhà hàng, hãy trả lời "Tôi xin lỗi, tôi không biết về điều này."

            Câu hỏi của người dùng: '{user_input}'
            Câu trả lời: """
            try:
                response = model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                print(f"Lỗi NLP: {e}")
                return "Tôi đang suy nghĩ..."
        else:
            return "Tôi xin lỗi, tôi không biết về điều này."

def find_nearby_restaurants_google(latitude_str, longitude_str):
    try:
        latitude = float(latitude_str)
        longitude = float(longitude_str)

        # Gọi trực tiếp Google Places API bằng requests
        api_key = settings.GOOGLE_API_KEY
        search_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            'location': f"{latitude},{longitude}",
            'radius': 500, # Tìm trong bán kính 500m
            'type': 'restaurant',
            'keyword': 'Korean restaurant',
            'key': api_key,
        }

        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])

        if results:
            restaurant_list = "Đây là một vài nhà hàng Hàn Quốc gần bạn:\n"
            for place in results:
                name = place.get('name', 'Không có tên')
                address = place.get('vicinity', 'Không có địa chỉ')
                restaurant_list += f"- **{name}**: {address}\n"
            return restaurant_list
        else:
            return "Không tìm thấy nhà hàng Hàn Quốc nào gần vị trí của bạn."

    except ValueError:
        return "Vị trí không hợp lệ."
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi Google Maps API: {e}")
        return "Có lỗi xảy ra khi tìm kiếm nhà hàng gần bạn."
    except Exception as e:
        print(f"Lỗi xử lý phản hồi Google Maps API: {e}")
        return "Có lỗi xảy ra khi xử lý thông tin nhà hàng."