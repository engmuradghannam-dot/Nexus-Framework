from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Language, Translation, TranslationImportJob
from .serializers import (
    LanguageListSerializer,
    LanguageSerializer,
    TranslationBulkCreateSerializer,
    TranslationImportJobSerializer,
    TranslationSearchSerializer,
    TranslationSerializer,
)


@extend_schema_view(
    list=extend_schema(tags=["i18n"], summary="List languages"),
    retrieve=extend_schema(tags=["i18n"], summary="Get language details"),
    create=extend_schema(tags=["i18n"], summary="Create language"),
    update=extend_schema(tags=["i18n"], summary="Update language"),
    destroy=extend_schema(tags=["i18n"], summary="Delete language"),
)
class LanguageViewSet(viewsets.ModelViewSet):
    queryset = Language.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return LanguageListSerializer
        return LanguageSerializer

    @extend_schema(tags=["i18n"], summary="Get default language")
    @action(detail=False, methods=["get"])
    def default(self, request):
        lang = Language.objects.filter(is_default=True).first()
        if not lang:
            lang = Language.objects.filter(code="en").first()
        serializer = LanguageSerializer(lang)
        return Response(serializer.data)

    @extend_schema(tags=["i18n"], summary="List active languages only")
    @action(detail=False, methods=["get"])
    def active(self, request):
        langs = Language.objects.filter(is_active=True)
        serializer = LanguageListSerializer(langs, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=["i18n"], summary="List translations"),
    retrieve=extend_schema(tags=["i18n"], summary="Get translation details"),
    create=extend_schema(tags=["i18n"], summary="Create translation"),
    update=extend_schema(tags=["i18n"], summary="Update translation"),
    destroy=extend_schema(tags=["i18n"], summary="Delete translation"),
)
class TranslationViewSet(viewsets.ModelViewSet):
    queryset = Translation.objects.all().select_related("language")
    serializer_class = TranslationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["language", "context", "is_reviewed"]
    search_fields = ["key", "value"]

    @extend_schema(
        tags=["i18n"],
        summary="Bulk create/update translations",
        request=TranslationBulkCreateSerializer,
    )
    @action(detail=False, methods=["post"])
    def bulk(self, request):
        serializer = TranslationBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        language = data["language"]
        translations_data = data["translations"]

        created = 0
        updated = 0
        for item in translations_data:
            key = item.get("key", "")
            value = item.get("value", "")
            context = item.get("context", "")
            if not key:
                continue
            obj, was_created = Translation.objects.update_or_create(
                language=language, key=key, context=context,
                defaults={"value": value},
            )
            if was_created:
                created += 1
            else:
                updated += 1

        return Response(
            {"created": created, "updated": updated, "language": language.code},
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=["i18n"],
        summary="Search translations",
        request=TranslationSearchSerializer,
    )
    @action(detail=False, methods=["get", "post"])
    def search(self, request):
        # Accept params from the query string (GET) or the body (POST).
        source = request.query_params if request.method == "GET" else request.data
        q = source.get("q")
        language = source.get("language")
        context = source.get("context")

        qs = Translation.objects.all().select_related("language")
        if q:
            qs = qs.filter(key__icontains=q) | qs.filter(value__icontains=q)
        if language:
            qs = qs.filter(language__code=language)
        if context:
            qs = qs.filter(context__icontains=context)

        page = self.paginate_queryset(qs)
        if page is not None:
            result_serializer = TranslationSerializer(page, many=True)
            return self.get_paginated_response(result_serializer.data)
        result_serializer = TranslationSerializer(qs[:100], many=True)
        return Response(result_serializer.data)

    @extend_schema(tags=["i18n"], summary="Get translations by language code")
    @action(detail=False, methods=["get"], url_path="by-language/(?P<code>[^/.]+)")
    def by_language(self, request, code=None):
        language = get_object_or_404(Language, code=code)
        translations = Translation.objects.filter(language=language)
        result = {t.key: t.value for t in translations}
        return Response({"language": code, "translations": result})


@extend_schema_view(
    list=extend_schema(tags=["i18n"], summary="List translation import jobs"),
    retrieve=extend_schema(tags=["i18n"], summary="Get import job details"),
    create=extend_schema(tags=["i18n"], summary="Create import job"),
)
class TranslationImportJobViewSet(viewsets.ModelViewSet):
    queryset = TranslationImportJob.objects.all().select_related("language")
    serializer_class = TranslationImportJobSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["language", "status"]
