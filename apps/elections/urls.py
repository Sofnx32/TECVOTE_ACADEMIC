from django.urls import path, include
from rest_framework_nested import routers
from .views import (
    ElectionViewSet,
    PositionViewSet,
    CandidateListViewSet,
    CandidacyViewSet,
    ElectionRuleViewSet,
)
from .views import FacultyListCreateView, AcademicPeriodListCreateView

router = routers.SimpleRouter()
router.register(r'elections', ElectionViewSet, basename='election')

elections_router = routers.NestedSimpleRouter(router, r'elections', lookup='election')
elections_router.register(r'positions', PositionViewSet, basename='election-positions')
elections_router.register(r'candidate-lists', CandidateListViewSet, basename='election-candidate-lists')
elections_router.register(r'rules', ElectionRuleViewSet, basename='election-rules')



positions_router = routers.NestedSimpleRouter(elections_router, r'positions', lookup='position')
positions_router.register(r'candidacies', CandidacyViewSet, basename='position-candidacies')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(elections_router.urls)),
    path('', include(positions_router.urls)),
]

urlpatterns += [
    path('faculties/', FacultyListCreateView.as_view(), name='faculty-list-create'),
    path('periods/', AcademicPeriodListCreateView.as_view(), name='academic-period-list-create'),
]