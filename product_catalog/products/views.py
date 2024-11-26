from django.shortcuts import get_object_or_404
from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Product
from .serializers import ProductSerializer

CACHE_TIMEOUT = 600  # 10 minutes

@api_view(['GET', 'POST'])
def product_list(request):
    if request.method == 'GET':
        cache_key = f"product_list:{request.GET}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        products = Product.objects.all()

        # Filtering
        category = request.GET.get('category')
        price_min = request.GET.get('price_min')
        price_max = request.GET.get('price_max')

        if category:
            products = products.filter(category=category)
        if price_min:
            products = products.filter(price__gte=price_min)
        if price_max:
            products = products.filter(price__lte=price_max)

        serializer = ProductSerializer(products, many=True)
        cache.set(cache_key, serializer.data, timeout=CACHE_TIMEOUT)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            cache.clear()  # Invalidate all caches
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def product_detail(request, pk):
    cache_key = f"product_detail:{pk}"

    if request.method == 'GET':
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product)
        cache.set(cache_key, serializer.data, timeout=CACHE_TIMEOUT)
        return Response(serializer.data)

    elif request.method == 'PUT':
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            cache.delete(cache_key)  # Invalidate cache
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        cache.delete(cache_key)  # Invalidate cache
        return Response(status=status.HTTP_204_NO_CONTENT)
