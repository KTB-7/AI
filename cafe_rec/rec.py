import pandas as pd
from lightfm import LightFM
from lightfm.data import Dataset
import numpy as np

# 사용자 데이터프레임
users_df = pd.DataFrame({
    'user_id': [1, 2, 3, 4, 5, 6],
    'user_tags': [
        ['#맛없음', '#최악의 커피', '#넓은 공간', '#친절도 부족', '#분위기 좋음', '#긍정적 경험'],
        ['#커피맛집', '#디저트', '#조용한', '#카공', '#편안함', '#친절한 직원', '#불친절', '#대기시간 길음', '#대형카페'],
        ['#뷰가좋은', '#테라스', '#브런치'],
        [],
        ['#전통카페', '#편안한', '#넓은공간', '#데이트하기 좋음', '#깔끔한 인테리어', '#혼잡', '#고객서비스 불만', '#맛있는 티라미수'],
        ['#향기좋은', '#디저트다양', '#힙한', '#조용한', '#친절한 직원', '#시간 낭비', '#가성비', '#책읽기 좋음', '#라떼맛집', '#긍정적 경험', '#부정적 경험']
        ],

    'user_tag_counts': [
        {'#맛없음': 1, '#최악의 커피': 2, '#넓은 공간': 5, '#친절도 부족': 3, '#분위기 좋음': 4, '#긍정적 경험': 2},
        {'#커피맛집': 4, '#디저트': 6, '#조용한': 3, '#카공': 5, '#편안함': 3, '#친절한 직원': 4, '#불친절': 2, '#대기시간 길음': 1, '#대형카페': 2},
        {'#뷰가좋은': 2, '#테라스': 1, '#브런치': 1},
        {},
        {'#전통카페': 5, '#편안한': 3, '#넓은공간': 2, '#데이트하기 좋음': 4, '#깔끔한 인테리어': 3, '#혼잡': 1, '#고객서비스 불만': 2, '#맛있는 티라미수': 5},
        {'#향기좋은': 2, '#디저트다양': 3, '#힙한': 4, '#조용한': 3, '#친절한 직원': 5, '#시간 낭비': 1, '#가성비': 4, '#책읽기 좋음': 3, '#라떼맛집': 2, '#긍정적 경험': 3, '#부정적 경험': 1}],
    })

# 카페 데이터프레임
cafes_df = pd.DataFrame({
    'place_id': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120],
    'place_tags': [
        ['#직원 불친절', '#가성비', '#넓은 공간', '#테라스'],
        ['#조용한', '#편한안', '#친절'],
        [],
        ['#전통카페', '#편안한', '#넓은공간', '#데이트하기 좋음', '#깔끔한 인테리어', '#혼잡', '#고객서비스 불만', '#맛있는 티라미수'],
        ['#향기좋은', '#디저트다양', '#힙한', '#조용한', '#친절한 직원', '#시간 낭비', '#가성비', '#책읽기 좋음', '#라떼맛집', '#긍정적 경험', '#부정적 경험'],
        ['#인스타', '#자주 감', '#아메리카노', '#친절한 서비스', '#무난무난', '#깨끗한 환경'],
        [],
        ['#회사 근처', '#사람이 많은', '#인기 카페', '#추천'],
        ['#맛없는 음료', '#잘못된 음료', '#시끌벅적한 분위기', '#블랙햅쌀고봉라떼', '#불편한 경험'],
        ['#맛있는 케이크', '#넓은 매장','#긍정적 경험', '#예쁜 케이크'],
        ['#조명 분위기', '#편안한 의자', '#수제 디저트', '#친절한 직원'],
        ['#모던 인테리어', '#빠른 서비스', '#친환경', '#와이파이 무료'],
        ['#애완동물 동반', '#저렴한 가격', '#홈메이드 케이크'],
        ['#뷰 좋은', '#신선한 원두', '#조용한 공간', '#다양한 메뉴'],
        ['#작은 공간', '#개인 작업 공간', '#편리한 위치'],
        ['#라이브 음악', '#바리스타 추천', '#계절 메뉴', '#넓은 공간'],
        ['#신상 음료', '#친근한 분위기', '#단체 손님 가능'],
        [],
        ['#빈티지 스타일', '#레트로 가구', '#편안한 분위기'],
        ['#아늑한 분위기', '#책과 커피', '#장인 정신']
    ],
    'place_tag_counts': [
        {'#직원 불친절': 2, '#가성비': 4, '#넓은 공간': 5, '#테라스': 1},
        {'#조용한':1, '#편한안':1, '#친절':1},
        {},
        {'#전통카페': 1, '#편안한': 3, '#넓은공간': 2, '#데이트하기 좋음': 4, '#깔끔한 인테리어': 3, '#혼잡': 4, '#고객서비스 불만': 2, '#맛있는 티라미수': 1},
        {'#향기좋은': 2, '#디저트다양': 3, '#힙한': 4, '#조용한': 3, '#친절한 직원': 5, '#시간 낭비': 1, '#가성비': 4, '#책읽기 좋음': 3, '#라떼맛집': 2, '#긍정적 경험': 3, '#부정적 경험': 1},
        {'#인스타': 3, '#자주 감' : 1, '#아메리카노' : 5, '#친절한 서비스' : 2, '#무난무난' : 1, '#깨끗한 환경' : 1},
        {},
        {'#회사 근처' : 1, '#사람이 많은' : 1, '#인기 카페' : 1, '#추천' : 3},
        {'#맛없는 음료' : 2, '#잘못된 음료' : 1, '#시끌벅적한 분위기' : 1, '#블랙햅쌀고봉라떼' : 1, '#불편한 경험' : 5},
        {'#맛있는 케이크' : 3, '#넓은 매장' : 2,'#긍정적 경험' : 1, '#예쁜 케이크' : 1},
        {'#조명 분위기': 2, '#편안한 의자': 3, '#수제 디저트': 4, '#친절한 직원': 2},
        {'#모던 인테리어': 3, '#빠른 서비스': 5, '#친환경': 2, '#와이파이 무료': 4},
        {'#애완동물 동반': 1, '#저렴한 가격': 3, '#홈메이드 케이크': 2},
        {'#뷰 좋은': 4, '#신선한 원두': 3, '#조용한 공간': 2, '#다양한 메뉴': 5},
        {'#작은 공간': 1, '#개인 작업 공간': 2, '#편리한 위치': 3},
        {'#라이브 음악': 2, '#바리스타 추천': 4, '#계절 메뉴': 3, '#넓은 공간':1},
        {'#신상 음료': 5, '#친근한 분위기': 3, '#단체 손님 가능': 2},
        {},
        {'#빈티지 스타일': 3, '#레트로 가구': 2, '#편안한 분위기': 4},
        {'#아늑한 분위기': 3, '#책과 커피': 2, '#장인 정신': 1}
    ]
})

# 상호작용 데이터 생성
interactions_data = []

for user_idx, user_row in users_df.iterrows():
    for cafe_idx, cafe_row in cafes_df.iterrows():
        common_tags = set(user_row['user_tags']).intersection(set(cafe_row['place_tags']))
        interaction_strength = sum([user_row['user_tag_counts'].get(tag, 0) for tag in common_tags])

        if interaction_strength > 0:
            interactions_data.append({
                'user_id': user_row['user_id'],
                'place_id': cafe_row['place_id'],
                'interaction': interaction_strength
            })
# 상호작용 데이터프레임 생성
interactions_df = pd.DataFrame(interactions_data)
print("상호작용 데이터프레임:")
print(interactions_df)

dataset = Dataset()

# 사용자와 아이템 특성 등록
# '#' 제거
user_features = set()
for tags in users_df['user_tags']:
    user_features.update([tag.lstrip('#') for tag in tags])

item_features = set()
for tags in cafes_df['place_tags']:
    item_features.update([tag.lstrip('#') for tag in tags])

dataset.fit(
    users=users_df['user_id'],
    items=cafes_df['place_id'],
    user_features=user_features,
    item_features=item_features
)

# 상호작용과 가중치 생성
# LightFM의 build_interactions은 (user, item, weight) 형태의 튜플을 허용합니다.
interactions_tuples = list(zip(interactions_df['user_id'], interactions_df['place_id'], interactions_df['interaction']))
(interactions, weights_matrix) = dataset.build_interactions(interactions_tuples)

user_feature_matrix = dataset.build_user_features([
    (row['user_id'], [tag.lstrip('#') for tag in row['user_tags']]) for idx, row in users_df.iterrows()
])

item_feature_matrix = dataset.build_item_features([
    (row['place_id'], [tag.lstrip('#') for tag in row['place_tags']]) for idx, row in cafes_df.iterrows()
])

model = LightFM(loss='warp', learning_rate=0.05, no_components=30, item_alpha=1e-6, user_alpha=1e-6)
model.fit(
    interactions,
    sample_weight=weights_matrix,
    user_features=user_feature_matrix,
    item_features=item_feature_matrix,
    epochs=30,
    num_threads=4
)

# 추천 생성
def recommend_cafes(model, dataset, user_id, cafes_df, user_features_matrix, item_features_matrix):
    user_internal_id = dataset.mapping()[0][user_id]
    all_item_ids = np.arange(dataset.interactions_shape()[1])

    # 이미 상호작용한 아이템 가져오기
    interacted_items = interactions_df[interactions_df['user_id'] == user_id]['place_id'].tolist()
    interacted_item_internal_ids = [dataset.mapping()[2][item] for item in interacted_items]

    # 모델을 사용하여 모든 아이템에 대한 점수 예측
    scores = model.predict(
        user_internal_id,
        all_item_ids,
        user_features=user_features_matrix,
        item_features=item_features_matrix
    )

    # 아이템과 점수를 데이터프레임으로 변환
    scores_df = pd.DataFrame({
        'place_id': cafes_df['place_id'],
        'score': scores
    })

    # 이미 상호작용한 아이템 제외
    scores_df = scores_df[~scores_df['place_id'].isin(interacted_items)]

    # 점수 기준 내림차순 정렬
    scores_df = scores_df.sort_values(by='score', ascending=False)
    recommended_place_ids = scores_df['place_id'].tolist()

    return recommended_place_ids

# 사용자 ID 설정
user_id = 1

# 추천 함수 호출
recommended_cafes = recommend_cafes(
    model,
    dataset,
    user_id,
    cafes_df,
    user_feature_matrix,
    item_feature_matrix,
)
print("\n사용자에게 추천하는 카페 (추천 점수 순):")
print(recommended_cafes)
