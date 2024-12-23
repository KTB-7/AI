import pandas as pd
import numpy as np
from collections import defaultdict
from typing import List, Tuple, Union
from lightfm import LightFM
from lightfm.data import Dataset

dataset = Dataset()

async def recommend_cafe(
    user_features: List[Union[int, str]],
    item_features: List[Union[int, str]],
    user_item_interactions: List[Union[int, str]],
    user_id_list: List[int],
    place_ids_list: List[List[int]]
) -> List[List[str]]:
    # print(user_features)
    # print(item_features)
    # print(user_item_interactions)

    userF1 = set()
    userF2 = set()
    itemF1 = set()
    itemF2 = set()

    for user in user_features:
        userF1.add(user[0])
        # userF2.add(user[1])
        if isinstance(user[1], int):
            userF2.add(str(user[1]))
        else:
            userF2.add(user[1])
    for item in item_features:
        itemF1.add(item[0])
        if isinstance(item[1], int):
            itemF2.add(str(item[1]))
        elif isinstance(item[1], float):
            itemF2.add(str(item[1]))
        else:
            itemF2.add(item[1])

    dataset.fit(
        users=userF1,
        items=itemF1,
        user_features=userF2,
        item_features=itemF2
    )

    # print("user_id_list\n", user_id_list)
    # print("place_ids_list\n", place_ids_list)
    # print("dataset fit users\n", userF1)
    # print("dataset fit items\n", itemF1)
    # print("dataset fit user_features\n", userF2)
    # print("dataset fit item_features\n", itemF2)
    # print("interactions\n", user_item_interactions)
    """
    user_feature_matrix = dataset.build_user_features([
    (row['user_id'], [tag.lstrip('#') for tag in row['user_tags']]) for idx, row in users_df.iterrows()
    ])
    """

    grouped_features = defaultdict(list)
    for user_id, feature in user_features:
        if isinstance(feature, int):
            feature = str(feature)
        grouped_features[user_id].append(feature)
    user_res = [(key, value) for key, value in grouped_features.items()]
    # print("user_res\n\n", user_res)

    grouped_features = defaultdict(list)
    for item_id, feature in item_features:
        if isinstance(feature, int):
            feature = str(feature)
        elif isinstance(feature, float):
            feature = str(feature)
        grouped_features[item_id].append(feature)
    item_res = [(key, value) for key, value in grouped_features.items()]
    # print("item_res\n\n", item_res)
            
    user_res = sorted(user_res, key=lambda x: x[0])
    item_res = sorted(item_res, key=lambda x: x[0])
    user_item_interactions = sorted(user_item_interactions, key=lambda x: (x[0], x[1]))
    # print("interactions\n", user_item_interactions)

    user_feature_matrix = dataset.build_user_features(user_res)
    item_feature_matrix = dataset.build_item_features(item_res)
    (interactions, weights_matrix) = dataset.build_interactions(user_item_interactions)

    model = LightFM(loss='warp', learning_rate=0.05, no_components=30, item_alpha=1e-6, user_alpha=1e-6)
    model.fit(
        interactions=interactions,
        sample_weight=weights_matrix,
        user_features=user_feature_matrix,
        item_features=item_feature_matrix,
        epochs=30
        # num_threads=2 # aws core 수를 모름
    )
    # print("interactions\n", interactions)
    # print("weights_matrix\n", weights_matrix)
    # print("user_feature_matrix\n", user_feature_matrix)
    # print("item_feature_matrix\n", item_feature_matrix)
    # print('\n\n\n\n')

    ret_list = []
    no_matching_item = []
    for user_id, place_ids in zip(user_id_list, place_ids_list):
        user_internal_id = dataset.mapping()[0][user_id]
        item_internal_id = []
        new_place_ids = []
        for item in place_ids:
            try:
                item_internal_id.append(dataset.mapping()[2][item])
                new_place_ids.append(item)
            except KeyError:
                no_matching_item.append(item)
        item_internal_id = np.array(item_internal_id)

        score = model.predict(
            user_ids=user_internal_id,
            item_ids=item_internal_id,
            user_features=user_feature_matrix,
            item_features=item_feature_matrix
        )

        # print("scores user\n", user_internal_id)
        # print("scores all items\n", item_internal_id)
        # print("scores user_features\n", user_feature_matrix)
        # print("scores item_features\n", item_feature_matrix)

        # print("user_id\n", user_id)
        # print("score\n\n",score)

        scores_df = pd.DataFrame({
            'item_id': list(new_place_ids),
            'score': list(score)
        })

        scores_df = scores_df.sort_values(by='score', ascending=False)
        recommend_place_ids = scores_df['item_id'].tolist()
        if no_matching_item:
            recommend_place_ids += no_matching_item
        recommend_place_ids = list(map(str, recommend_place_ids))

        # print("recommend_place_ids\n\n", recommend_place_ids)

        ret_list.append(recommend_place_ids)
    user_id_list = list(map(str, user_id_list))
    

    return user_id_list, ret_list