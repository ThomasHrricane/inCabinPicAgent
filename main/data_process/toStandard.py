import json

def fill_standard_input(data, standard_template):
    """
    使用提供的数据填充standardInput模板中的tag_list。

    Args:
        data (dict): 包含车辆、人员、物品和宠物信息的字典。
        standard_template (dict): 包含完整结构的standardInput JSON模板。

    Returns:
        dict: 已填充好value的standardInput字典。
    """
    # 创建模板的深拷贝以避免修改原始模板
    output_json = json.loads(json.dumps(standard_template))

    # --- 位置映射辅助函数 ---
    def map_location(location_str):
        """
        根据规则转换位置名称。
        此函数同时处理人员、物品和宠物的位置映射。
        """
        mapping = {
            # 人员位置映射
            "前排左": "副驾",
            "前排右": "主驾",
            "中排左（若有）": "二排右",
            "中排右（若有）": "二排左",
            "后排左": "三排右",
            "后排右": "三排左",
            # 物品/宠物特定位置映射
            "中央扶手箱": "前排扶手箱",
            "中央扶手箱-杯槽": "前排扶手箱-杯槽"
        }
        # .get()方法可以在找不到键时返回一个默认值（这里是'UNKNOWN'）
        return [mapping.get(location_str, "UNKNOWN")]

    # 为了方便快速地更新value，创建一个从tag_key到tag对象的映射字典
    tag_list = output_json['label_result']['global']['100000'][0]['tag_list']
    tag_map = {tag['tag_key']: tag for tag in tag_list}

    # --- 1. 填充全局顶层信息 ---
    tag_map['是否抛弃']['value'] = '可用'
    tag_map['车内人数']['value'] = data.get('人', {}).get('人数', '0')
    tag_map['车内物品数']['value'] = data.get('物品', {}).get('物品数', '0')
    tag_map['车内宠物数']['value'] = data.get('宠物', {}).get('宠物数', '0')
    tag_map['晚上']['value'] = '晚上' if data.get('是否为黑夜') == '是' else '否'
    tag_map['摄像头位置']['value'] = '一排' if data.get('是否有中央扶手箱') == '是' else '二排'

    # --- 2. 填充人员详细信息 ---
    persons_data = data.get('人', {}).get('具体信息', [])
    for i, person in enumerate(persons_data):
        person_num = i + 1
        # 动态构建tag_key并更新对应的值
        tag_map[f'person{person_num}-年龄']['value'] = person.get('年龄', 'UNKNOWN')
        tag_map[f'person{person_num}-性别']['value'] = person.get('性别', 'UNKNOWN')
        tag_map[f'person{person_num}-位置']['value'] = map_location(person.get('位置'))
        
        # 行为按要求不填充
        tag_map[f'person{person_num}-行为']['value'] = []
        
        # 着装1: 上衣样式 + 配饰
        clothing1_types = []
        if person.get('上衣样式'): clothing1_types.append(person['上衣样式'])
        if person.get('配饰'): clothing1_types.append(person['配饰'])
        tag_map[f'person{person_num}-衣裤-着装1类型']['value'] = clothing1_types
        
        # 着装1颜色: 上衣颜色 (处理逗号分隔的多个颜色)
        upper_colors = [color.strip() for color in person.get('上衣颜色', '').split(',') if color]
        tag_map[f'person{person_num}-衣裤-着装1颜色']['value'] = upper_colors
        
        # 着装2: 下装样式
        lower_style = person.get('下装样式')
        tag_map[f'person{person_num}-衣裤-着装2类型']['value'] = [lower_style] if lower_style else []
        
        # 着装2颜色: 下装颜色 (处理逗号分隔的多个颜色)
        lower_colors = [color.strip() for color in person.get('下装颜色', '').split(',') if color]
        tag_map[f'person{person_num}-衣裤-着装2颜色']['value'] = lower_colors

    # --- 3. 填充物品详细信息 ---
    items_data = data.get('物品', {}).get('具体信息', [])
    for i, item in enumerate(items_data):
        item_num = i + 1
        tag_map[f'good{item_num}-种类']['value'] = item.get('种类', 'UNKNOWN')
        tag_map[f'good{item_num}-位置']['value'] = map_location(item.get('位置'))

    # --- 4. 填充宠物详细信息 ---
    pets_data = data.get('宠物', {}).get('具体信息', [])
    for i, pet in enumerate(pets_data):
        pet_num = i + 1
        tag_map[f'pet{pet_num}-种类']['value'] = pet.get('种类', 'UNKNOWN')
        tag_map[f'pet{pet_num}-位置']['value'] = map_location(pet.get('位置'))
        
    return output_json


# --- 输入数据 ---

# 1. 这是您提供的完整的standardInput.json结构，作为模板

# 注意: 为了简洁, 上述模板仅显示了部分tag项。在实际运行时, 请确保此变量包含您提供的完整的JSON结构。
# 您的完整JSON结构已被加载到初始问题中，代码会假定此变量持有该完整结构。


# 2. 这是需要嵌入到模板中的业务数据
data_to_embed = {
    "是否为黑夜": "否",
    "是否有中央扶手箱": "是",
    "人": {
        "人数": "4",
        "具体信息": [
            {"性别": "女性", "年龄": "成年", "位置": "前排左", "上衣颜色": "白色", "上衣样式": "连帽衫", "下装颜色": "白色", "下装样式": "休闲长裤", "配饰": "眼镜"},
            {"性别": "女性", "年龄": "成年", "位置": "后排左", "上衣颜色": "米色,棕色", "上衣样式": "衬衫", "下装颜色": "unknown", "下装样式": "unknown", "配饰": "眼镜"},
            {"性别": "unknown", "年龄": "儿童", "位置": "中排右（若有）", "上衣颜色": "蓝色", "上衣样式": "T恤", "下装颜色": "米色", "下装样式": "短裤", "配饰": "眼镜"},
            {"性别": "unknown", "年龄": "儿童", "位置": "中排左（若有）", "上衣颜色": "黑色,白色", "上衣样式": "T恤", "下装颜色": "unknown", "下装样式": "短裤", "配饰": "眼镜"}
        ]
    },
    "物品": {
        "物品数": "5",
        "具体信息": [
            {"种类": "外套", "位置": "中央扶手箱"},
            {"种类": "水杯", "位置": "中央扶手箱-杯槽"},
            {"种类": "钥匙", "位置": "中央扶手箱-杯槽"},
            {"种类": "平板", "位置": "前排右"},
            {"种类": "手机", "位置": "前排左"}
        ]
    },
    "宠物": {
        "宠物数": "2",
        "具体信息": [
            {"种类": "狗", "位置": "中排左（若有）"},
            {"种类": "狗", "位置": "后排右"}
        ]
    },
    "id": 61
}


# --- 主程序执行 ---
if __name__ == "__main__":
    # 从您上传的文件内容中加载完整的JSON模板
    # (在实际环境中, 您可能需要从文件中读取 `standardInput.json`)
    # full_standardInput_template = json.loads(open('./standardInput.json', 'r', encoding='utf-8').read())
    
    # 调用函数处理数据


    standardInput_template = {
    "id": 15700662,
    "order_info": [
        {
            "content_id": "0",
            "dataset_header_id": 0,
            "type": "text",
            "view_name": "id",
            "value": "1"
        },
        {
            "content_id": "1",
            "dataset_header_id": 1,
            "type": "image",
            "view_name": "url",
            "value": "https://annotation-black.obs.cn-north-4.myhuaweicloud.com/manual/cheji/sync/大众评测集宠物0905五座车/DJI_20250905142433_0276_D.JPG"
        }
    ],
    "label_result": {
        "global": {
            "100000": [
                {
                    "ext_info": "null",
                    "flow_type": "100000",
                    "group_id": "d3747244-54e3-4c35-89b9-dd518c86e704",
                    "group_type": "single_text",
                    "order_content_id": "",
                    "tag_list": [
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "抛弃",
                                    "value": "抛弃"
                                },
                                {
                                    "name": "可用",
                                    "value": "可用"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "dc17a1fd-6fab-42e7-b15d-abdfc1a74910",
                            "tag_key": "是否抛弃",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "是否抛弃"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "dc17a1fd-6fab-42e7-b15d-abdfc1a74910",
                                "depends_value": [
                                    "可用"
                                ],
                                "option": [
                                    {
                                        "label": "抛弃",
                                        "value": "抛弃"
                                    },
                                    {
                                        "label": "可用",
                                        "value": "可用"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "0",
                                    "value": "0"
                                },
                                {
                                    "name": "1",
                                    "value": "1"
                                },
                                {
                                    "name": "2",
                                    "value": "2"
                                },
                                {
                                    "name": "3",
                                    "value": "3"
                                },
                                {
                                    "name": "4",
                                    "value": "4"
                                },
                                {
                                    "name": "5",
                                    "value": "5"
                                },
                                {
                                    "name": "6",
                                    "value": "6"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                            "tag_key": "车内人数",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "车内人数"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "dc17a1fd-6fab-42e7-b15d-abdfc1a74910",
                                "depends_value": [
                                    "可用"
                                ],
                                "option": [
                                    {
                                        "label": "抛弃",
                                        "value": "抛弃"
                                    },
                                    {
                                        "label": "可用",
                                        "value": "可用"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "0",
                                    "value": "0"
                                },
                                {
                                    "name": "1",
                                    "value": "1"
                                },
                                {
                                    "name": "2",
                                    "value": "2"
                                },
                                {
                                    "name": "3",
                                    "value": "3"
                                },
                                {
                                    "name": "4",
                                    "value": "4"
                                },
                                {
                                    "name": "5",
                                    "value": "5"
                                },
                                {
                                    "name": "6",
                                    "value": "6"
                                },
                                {
                                    "name": "7",
                                    "value": "7"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                            "tag_key": "车内物品数",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "车内物品数"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "dc17a1fd-6fab-42e7-b15d-abdfc1a74910",
                                "depends_value": [
                                    "可用"
                                ],
                                "option": [
                                    {
                                        "label": "抛弃",
                                        "value": "抛弃"
                                    },
                                    {
                                        "label": "可用",
                                        "value": "可用"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "0",
                                    "value": "0"
                                },
                                {
                                    "name": "1",
                                    "value": "1"
                                },
                                {
                                    "name": "2",
                                    "value": "2"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "410f81f1-edb3-46bb-82da-2ce866aff978",
                            "tag_key": "车内宠物数",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "车内宠物数"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "dc17a1fd-6fab-42e7-b15d-abdfc1a74910",
                                "depends_value": [
                                    "可用"
                                ],
                                "option": [
                                    {
                                        "label": "抛弃",
                                        "value": "抛弃"
                                    },
                                    {
                                        "label": "可用",
                                        "value": "可用"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "晚上",
                                    "value": "晚上"
                                },
                                {
                                    "name": "否",
                                    "value": "否"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "5698eb13-d097-41b6-8e78-601f4fbc1826",
                            "tag_key": "晚上",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "晚上"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "1",
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "婴幼儿",
                                    "value": "婴幼儿"
                                },
                                {
                                    "name": "儿童",
                                    "value": "儿童"
                                },
                                {
                                    "name": "成年",
                                    "value": "成年"
                                },
                                {
                                    "name": "老年",
                                    "value": "老年"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "00ebd55a-c23b-47cd-9b6c-3b20b125bfe0",
                            "tag_key": "person1-年龄",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "person1-年龄"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "1",
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "男性",
                                    "value": "男性"
                                },
                                {
                                    "name": "女性",
                                    "value": "女性"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "920a11c7-9337-4a06-a5d6-984dee33cf0d",
                            "tag_key": "person1-性别",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "person1-性别"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "1",
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "496aaeae-5f21-42b7-bfd6-5837648a435b",
                            "tag_key": "person1-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person1-位置"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "1",
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "阅读",
                                    "value": "阅读"
                                },
                                {
                                    "name": "化妆",
                                    "value": "化妆"
                                },
                                {
                                    "name": "吃东西",
                                    "value": "吃东西"
                                },
                                {
                                    "name": "托腮思考",
                                    "value": "托腮思考"
                                },
                                {
                                    "name": "玩手机",
                                    "value": "玩手机"
                                },
                                {
                                    "name": "打电话",
                                    "value": "打电话"
                                },
                                {
                                    "name": "吸烟",
                                    "value": "吸烟"
                                },
                                {
                                    "name": "点烟",
                                    "value": "点烟"
                                },
                                {
                                    "name": "睡觉",
                                    "value": "睡觉"
                                },
                                {
                                    "name": "抱猫",
                                    "value": "抱猫"
                                },
                                {
                                    "name": "抱狗",
                                    "value": "抱狗"
                                },
                                {
                                    "name": "头/手伸出窗外",
                                    "value": "头/手伸出窗外"
                                },
                                {
                                    "name": "哭闹",
                                    "value": "哭闹"
                                },
                                {
                                    "name": "未系安全带",
                                    "value": "未系安全带"
                                },
                                {
                                    "name": "全位置手势（食指伸出）前",
                                    "value": "全位置手势（食指伸出）前"
                                },
                                {
                                    "name": "全位置手势（食指伸出）上",
                                    "value": "全位置手势（食指伸出）上"
                                },
                                {
                                    "name": "全位置手势（食指伸出）下",
                                    "value": "全位置手势（食指伸出）下"
                                },
                                {
                                    "name": "全位置手势（食指伸出）左",
                                    "value": "全位置手势（食指伸出）左"
                                },
                                {
                                    "name": "全位置手势（食指伸出）右",
                                    "value": "全位置手势（食指伸出）右"
                                },
                                {
                                    "name": "手触碰屏幕",
                                    "value": "手触碰屏幕"
                                },
                                {
                                    "name": "站立",
                                    "value": "站立"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "71dced3a-2dea-4888-8426-c20130557bec",
                            "tag_key": "person1-行为",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person1-行为"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "1",
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "T恤",
                                    "value": "T恤"
                                },
                                {
                                    "name": "衬衫",
                                    "value": "衬衫"
                                },
                                {
                                    "name": "毛衣",
                                    "value": "毛衣"
                                },
                                {
                                    "name": "夹克",
                                    "value": "夹克"
                                },
                                {
                                    "name": "连帽衫",
                                    "value": "连帽衫"
                                },
                                {
                                    "name": "polo衫",
                                    "value": "polo衫"
                                },
                                {
                                    "name": "西装",
                                    "value": "西装"
                                },
                                {
                                    "name": "大衣",
                                    "value": "大衣"
                                },
                                {
                                    "name": "羽绒服",
                                    "value": "羽绒服"
                                },
                                {
                                    "name": "眼镜",
                                    "value": "眼镜"
                                },
                                {
                                    "name": "围巾",
                                    "value": "围巾"
                                },
                                {
                                    "name": "帽子",
                                    "value": "帽子"
                                },
                                {
                                    "name": "耳机",
                                    "value": "耳机"
                                },
                                {
                                    "name": "手表",
                                    "value": "手表"
                                },
                                {
                                    "name": "马夹",
                                    "value": "马夹"
                                },
                                {
                                    "name": "墨镜",
                                    "value": "墨镜"
                                },
                                {
                                    "name": "口罩",
                                    "value": "口罩"
                                },
                                {
                                    "name": "连衣裙",
                                    "value": "连衣裙"
                                },
                                {
                                    "name": "背心",
                                    "value": "背心"
                                },
                                {
                                    "name": "耳坠（大）",
                                    "value": "耳坠（大）"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "e7f4d094-cb9f-4b37-9532-c3ab140518e1",
                            "tag_key": "person1-衣裤-着装1类型",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person1-衣裤-着装1类型"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "1",
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "灰色",
                                    "value": "灰色"
                                },
                                {
                                    "name": "红色",
                                    "value": "红色"
                                },
                                {
                                    "name": "蓝色",
                                    "value": "蓝色"
                                },
                                {
                                    "name": "橙色",
                                    "value": "橙色"
                                },
                                {
                                    "name": "黄色",
                                    "value": "黄色"
                                },
                                {
                                    "name": "绿色",
                                    "value": "绿色"
                                },
                                {
                                    "name": "紫色",
                                    "value": "紫色"
                                },
                                {
                                    "name": "黑色",
                                    "value": "黑色"
                                },
                                {
                                    "name": "白色",
                                    "value": "白色"
                                },
                                {
                                    "name": "棕色",
                                    "value": "棕色"
                                },
                                {
                                    "name": "粉色",
                                    "value": "粉色"
                                },
                                {
                                    "name": "金色",
                                    "value": "金色"
                                },
                                {
                                    "name": "银色",
                                    "value": "银色"
                                },
                                {
                                    "name": "米色",
                                    "value": "米色"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "7c351375-de2e-4a75-b4d3-72e6f9862a4f",
                            "tag_key": "person1-衣裤-着装1颜色",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person1-衣裤-着装1颜色"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "1",
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "裙子",
                                    "value": "裙子"
                                },
                                {
                                    "name": "牛仔长裤",
                                    "value": "牛仔长裤"
                                },
                                {
                                    "name": "西装长裤",
                                    "value": "西装长裤"
                                },
                                {
                                    "name": "休闲长裤",
                                    "value": "休闲长裤"
                                },
                                {
                                    "name": "短裤",
                                    "value": "短裤"
                                },
                                {
                                    "name": "靴子",
                                    "value": "靴子"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "9df7e7a2-a919-4e5a-9ba2-ac34e3843675",
                            "tag_key": "person1-衣裤-着装2类型",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person1-衣裤-着装2类型"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "1",
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "灰色",
                                    "value": "灰色"
                                },
                                {
                                    "name": "红色",
                                    "value": "红色"
                                },
                                {
                                    "name": "蓝色",
                                    "value": "蓝色"
                                },
                                {
                                    "name": "橙色",
                                    "value": "橙色"
                                },
                                {
                                    "name": "黄色",
                                    "value": "黄色"
                                },
                                {
                                    "name": "绿色",
                                    "value": "绿色"
                                },
                                {
                                    "name": "紫色",
                                    "value": "紫色"
                                },
                                {
                                    "name": "黑色",
                                    "value": "黑色"
                                },
                                {
                                    "name": "白色",
                                    "value": "白色"
                                },
                                {
                                    "name": "棕色",
                                    "value": "棕色"
                                },
                                {
                                    "name": "粉色",
                                    "value": "粉色"
                                },
                                {
                                    "name": "金色",
                                    "value": "金色"
                                },
                                {
                                    "name": "银色",
                                    "value": "银色"
                                },
                                {
                                    "name": "米色",
                                    "value": "米色"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "496e65ef-59e0-419f-8a40-ed6778b54ef4",
                            "tag_key": "person1-衣裤-着装2颜色",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person1-衣裤-着装2颜色"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "婴幼儿",
                                    "value": "婴幼儿"
                                },
                                {
                                    "name": "儿童",
                                    "value": "儿童"
                                },
                                {
                                    "name": "成年",
                                    "value": "成年"
                                },
                                {
                                    "name": "老年",
                                    "value": "老年"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "5acac5d1-ffb4-4bc0-bd38-d0237a06acaf",
                            "tag_key": "person2-年龄",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "person2-年龄"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "男性",
                                    "value": "男性"
                                },
                                {
                                    "name": "女性",
                                    "value": "女性"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "f2e410aa-28e4-4a11-a5ca-37c110788f20",
                            "tag_key": "person2-性别",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "person2-性别"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "9b479f7a-f3e0-47b5-b8f5-4bdf58fcad6c",
                            "tag_key": "person2-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person2-位置"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "阅读",
                                    "value": "阅读"
                                },
                                {
                                    "name": "化妆",
                                    "value": "化妆"
                                },
                                {
                                    "name": "吃东西",
                                    "value": "吃东西"
                                },
                                {
                                    "name": "托腮思考",
                                    "value": "托腮思考"
                                },
                                {
                                    "name": "玩手机",
                                    "value": "玩手机"
                                },
                                {
                                    "name": "打电话",
                                    "value": "打电话"
                                },
                                {
                                    "name": "吸烟",
                                    "value": "吸烟"
                                },
                                {
                                    "name": "点烟",
                                    "value": "点烟"
                                },
                                {
                                    "name": "睡觉",
                                    "value": "睡觉"
                                },
                                {
                                    "name": "抱猫",
                                    "value": "抱猫"
                                },
                                {
                                    "name": "抱狗",
                                    "value": "抱狗"
                                },
                                {
                                    "name": "头/手伸出窗外",
                                    "value": "头/手伸出窗外"
                                },
                                {
                                    "name": "哭闹",
                                    "value": "哭闹"
                                },
                                {
                                    "name": "未系安全带",
                                    "value": "未系安全带"
                                },
                                {
                                    "name": "全位置手势（食指伸出）前",
                                    "value": "全位置手势（食指伸出）前"
                                },
                                {
                                    "name": "全位置手势（食指伸出）上",
                                    "value": "全位置手势（食指伸出）上"
                                },
                                {
                                    "name": "全位置手势（食指伸出）下",
                                    "value": "全位置手势（食指伸出）下"
                                },
                                {
                                    "name": "全位置手势（食指伸出）左",
                                    "value": "全位置手势（食指伸出）左"
                                },
                                {
                                    "name": "全位置手势（食指伸出）右",
                                    "value": "全位置手势（食指伸出）右"
                                },
                                {
                                    "name": "手触碰屏幕",
                                    "value": "手触碰屏幕"
                                },
                                {
                                    "name": "站立",
                                    "value": "站立"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "405a230b-823b-4453-b67c-50ccc60151a9",
                            "tag_key": "person2-行为",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person2-行为"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "T恤",
                                    "value": "T恤"
                                },
                                {
                                    "name": "衬衫",
                                    "value": "衬衫"
                                },
                                {
                                    "name": "毛衣",
                                    "value": "毛衣"
                                },
                                {
                                    "name": "夹克",
                                    "value": "夹克"
                                },
                                {
                                    "name": "连帽衫",
                                    "value": "连帽衫"
                                },
                                {
                                    "name": "polo衫",
                                    "value": "polo衫"
                                },
                                {
                                    "name": "西装",
                                    "value": "西装"
                                },
                                {
                                    "name": "大衣",
                                    "value": "大衣"
                                },
                                {
                                    "name": "羽绒服",
                                    "value": "羽绒服"
                                },
                                {
                                    "name": "眼镜",
                                    "value": "眼镜"
                                },
                                {
                                    "name": "围巾",
                                    "value": "围巾"
                                },
                                {
                                    "name": "帽子",
                                    "value": "帽子"
                                },
                                {
                                    "name": "耳机",
                                    "value": "耳机"
                                },
                                {
                                    "name": "手表",
                                    "value": "手表"
                                },
                                {
                                    "name": "马夹",
                                    "value": "马夹"
                                },
                                {
                                    "name": "墨镜",
                                    "value": "墨镜"
                                },
                                {
                                    "name": "口罩",
                                    "value": "口罩"
                                },
                                {
                                    "name": "连衣裙",
                                    "value": "连衣裙"
                                },
                                {
                                    "name": "背心",
                                    "value": "背心"
                                },
                                {
                                    "name": "耳坠（大）",
                                    "value": "耳坠（大）"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "81815018-c8b8-44e5-ad96-6e2512b70d59",
                            "tag_key": "person2-衣裤-着装1类型",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person2-衣裤-着装1类型"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "灰色",
                                    "value": "灰色"
                                },
                                {
                                    "name": "红色",
                                    "value": "红色"
                                },
                                {
                                    "name": "蓝色",
                                    "value": "蓝色"
                                },
                                {
                                    "name": "橙色",
                                    "value": "橙色"
                                },
                                {
                                    "name": "黄色",
                                    "value": "黄色"
                                },
                                {
                                    "name": "绿色",
                                    "value": "绿色"
                                },
                                {
                                    "name": "紫色",
                                    "value": "紫色"
                                },
                                {
                                    "name": "黑色",
                                    "value": "黑色"
                                },
                                {
                                    "name": "白色",
                                    "value": "白色"
                                },
                                {
                                    "name": "棕色",
                                    "value": "棕色"
                                },
                                {
                                    "name": "粉色",
                                    "value": "粉色"
                                },
                                {
                                    "name": "金色",
                                    "value": "金色"
                                },
                                {
                                    "name": "银色",
                                    "value": "银色"
                                },
                                {
                                    "name": "米色",
                                    "value": "米色"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "822d46d1-dbcf-470c-82ac-9783308abc08",
                            "tag_key": "person2-衣裤-着装1颜色",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person2-衣裤-着装1颜色"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "裙子",
                                    "value": "裙子"
                                },
                                {
                                    "name": "牛仔长裤",
                                    "value": "牛仔长裤"
                                },
                                {
                                    "name": "西装长裤",
                                    "value": "西装长裤"
                                },
                                {
                                    "name": "休闲长裤",
                                    "value": "休闲长裤"
                                },
                                {
                                    "name": "短裤",
                                    "value": "短裤"
                                },
                                {
                                    "name": "靴子",
                                    "value": "靴子"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "3a62acf3-0d30-4c73-914e-f5cdb79d9560",
                            "tag_key": "person2-衣裤-着装2类型",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person2-衣裤-着装2类型"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "灰色",
                                    "value": "灰色"
                                },
                                {
                                    "name": "红色",
                                    "value": "红色"
                                },
                                {
                                    "name": "蓝色",
                                    "value": "蓝色"
                                },
                                {
                                    "name": "橙色",
                                    "value": "橙色"
                                },
                                {
                                    "name": "黄色",
                                    "value": "黄色"
                                },
                                {
                                    "name": "绿色",
                                    "value": "绿色"
                                },
                                {
                                    "name": "紫色",
                                    "value": "紫色"
                                },
                                {
                                    "name": "黑色",
                                    "value": "黑色"
                                },
                                {
                                    "name": "白色",
                                    "value": "白色"
                                },
                                {
                                    "name": "棕色",
                                    "value": "棕色"
                                },
                                {
                                    "name": "粉色",
                                    "value": "粉色"
                                },
                                {
                                    "name": "金色",
                                    "value": "金色"
                                },
                                {
                                    "name": "银色",
                                    "value": "银色"
                                },
                                {
                                    "name": "米色",
                                    "value": "米色"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "a26d2218-fdd1-4c14-9818-c6ad901d5f34",
                            "tag_key": "person2-衣裤-着装2颜色",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person2-衣裤-着装2颜色"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "婴幼儿",
                                    "value": "婴幼儿"
                                },
                                {
                                    "name": "儿童",
                                    "value": "儿童"
                                },
                                {
                                    "name": "成年",
                                    "value": "成年"
                                },
                                {
                                    "name": "老年",
                                    "value": "老年"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "fa1290d2-21c9-497c-8a93-46fd5c86497a",
                            "tag_key": "person3-年龄",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "person3-年龄"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "男性",
                                    "value": "男性"
                                },
                                {
                                    "name": "女性",
                                    "value": "女性"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "e7d0d05d-091e-4402-adce-f40e1ef1db0f",
                            "tag_key": "person3-性别",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "person3-性别"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "42ff2951-15fd-4b06-8873-25e638135279",
                            "tag_key": "person3-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person3-位置"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "阅读",
                                    "value": "阅读"
                                },
                                {
                                    "name": "化妆",
                                    "value": "化妆"
                                },
                                {
                                    "name": "吃东西",
                                    "value": "吃东西"
                                },
                                {
                                    "name": "托腮思考",
                                    "value": "托腮思考"
                                },
                                {
                                    "name": "玩手机",
                                    "value": "玩手机"
                                },
                                {
                                    "name": "打电话",
                                    "value": "打电话"
                                },
                                {
                                    "name": "吸烟",
                                    "value": "吸烟"
                                },
                                {
                                    "name": "点烟",
                                    "value": "点烟"
                                },
                                {
                                    "name": "睡觉",
                                    "value": "睡觉"
                                },
                                {
                                    "name": "抱猫",
                                    "value": "抱猫"
                                },
                                {
                                    "name": "抱狗",
                                    "value": "抱狗"
                                },
                                {
                                    "name": "头/手伸出窗外",
                                    "value": "头/手伸出窗外"
                                },
                                {
                                    "name": "哭闹",
                                    "value": "哭闹"
                                },
                                {
                                    "name": "未系安全带",
                                    "value": "未系安全带"
                                },
                                {
                                    "name": "全位置手势（食指伸出）前",
                                    "value": "全位置手势（食指伸出）前"
                                },
                                {
                                    "name": "全位置手势（食指伸出）上",
                                    "value": "全位置手势（食指伸出）上"
                                },
                                {
                                    "name": "全位置手势（食指伸出）下",
                                    "value": "全位置手势（食指伸出）下"
                                },
                                {
                                    "name": "全位置手势（食指伸出）左",
                                    "value": "全位置手势（食指伸出）左"
                                },
                                {
                                    "name": "全位置手势（食指伸出）右",
                                    "value": "全位置手势（食指伸出）右"
                                },
                                {
                                    "name": "手触碰屏幕",
                                    "value": "手触碰屏幕"
                                },
                                {
                                    "name": "站立",
                                    "value": "站立"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "1cce553a-d8f8-45ad-a8c2-f4ab17c4f802",
                            "tag_key": "person3-行为",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person3-行为"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "T恤",
                                    "value": "T恤"
                                },
                                {
                                    "name": "衬衫",
                                    "value": "衬衫"
                                },
                                {
                                    "name": "毛衣",
                                    "value": "毛衣"
                                },
                                {
                                    "name": "夹克",
                                    "value": "夹克"
                                },
                                {
                                    "name": "连帽衫",
                                    "value": "连帽衫"
                                },
                                {
                                    "name": "polo衫",
                                    "value": "polo衫"
                                },
                                {
                                    "name": "西装",
                                    "value": "西装"
                                },
                                {
                                    "name": "大衣",
                                    "value": "大衣"
                                },
                                {
                                    "name": "羽绒服",
                                    "value": "羽绒服"
                                },
                                {
                                    "name": "眼镜",
                                    "value": "眼镜"
                                },
                                {
                                    "name": "围巾",
                                    "value": "围巾"
                                },
                                {
                                    "name": "帽子",
                                    "value": "帽子"
                                },
                                {
                                    "name": "耳机",
                                    "value": "耳机"
                                },
                                {
                                    "name": "手表",
                                    "value": "手表"
                                },
                                {
                                    "name": "马夹",
                                    "value": "马夹"
                                },
                                {
                                    "name": "墨镜",
                                    "value": "墨镜"
                                },
                                {
                                    "name": "口罩",
                                    "value": "口罩"
                                },
                                {
                                    "name": "连衣裙",
                                    "value": "连衣裙"
                                },
                                {
                                    "name": "背心",
                                    "value": "背心"
                                },
                                {
                                    "name": "耳坠（大）",
                                    "value": "耳坠（大）"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "19f5ce42-bbbb-4fcc-9b51-a9e5552c2e74",
                            "tag_key": "person3-衣裤-着装1类型",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person3-衣裤-着装1类型"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "灰色",
                                    "value": "灰色"
                                },
                                {
                                    "name": "红色",
                                    "value": "红色"
                                },
                                {
                                    "name": "蓝色",
                                    "value": "蓝色"
                                },
                                {
                                    "name": "橙色",
                                    "value": "橙色"
                                },
                                {
                                    "name": "黄色",
                                    "value": "黄色"
                                },
                                {
                                    "name": "绿色",
                                    "value": "绿色"
                                },
                                {
                                    "name": "紫色",
                                    "value": "紫色"
                                },
                                {
                                    "name": "黑色",
                                    "value": "黑色"
                                },
                                {
                                    "name": "白色",
                                    "value": "白色"
                                },
                                {
                                    "name": "棕色",
                                    "value": "棕色"
                                },
                                {
                                    "name": "粉色",
                                    "value": "粉色"
                                },
                                {
                                    "name": "金色",
                                    "value": "金色"
                                },
                                {
                                    "name": "银色",
                                    "value": "银色"
                                },
                                {
                                    "name": "米色",
                                    "value": "米色"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "e1ca66e7-0dd0-47e1-a66e-4a7197035780",
                            "tag_key": "person3-衣裤-着装1颜色",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person3-衣裤-着装1颜色"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "裙子",
                                    "value": "裙子"
                                },
                                {
                                    "name": "牛仔长裤",
                                    "value": "牛仔长裤"
                                },
                                {
                                    "name": "西装长裤",
                                    "value": "西装长裤"
                                },
                                {
                                    "name": "休闲长裤",
                                    "value": "休闲长裤"
                                },
                                {
                                    "name": "短裤",
                                    "value": "短裤"
                                },
                                {
                                    "name": "靴子",
                                    "value": "靴子"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "7fb597aa-f20d-4bc6-b93e-35be0ce78895",
                            "tag_key": "person3-衣裤-着装2类型",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person3-衣裤-着装2类型"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "3",
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "灰色",
                                    "value": "灰色"
                                },
                                {
                                    "name": "红色",
                                    "value": "红色"
                                },
                                {
                                    "name": "蓝色",
                                    "value": "蓝色"
                                },
                                {
                                    "name": "橙色",
                                    "value": "橙色"
                                },
                                {
                                    "name": "黄色",
                                    "value": "黄色"
                                },
                                {
                                    "name": "绿色",
                                    "value": "绿色"
                                },
                                {
                                    "name": "紫色",
                                    "value": "紫色"
                                },
                                {
                                    "name": "黑色",
                                    "value": "黑色"
                                },
                                {
                                    "name": "白色",
                                    "value": "白色"
                                },
                                {
                                    "name": "棕色",
                                    "value": "棕色"
                                },
                                {
                                    "name": "粉色",
                                    "value": "粉色"
                                },
                                {
                                    "name": "金色",
                                    "value": "金色"
                                },
                                {
                                    "name": "银色",
                                    "value": "银色"
                                },
                                {
                                    "name": "米色",
                                    "value": "米色"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "d913a3ca-f8bf-4847-a5e2-0458f90ce5e5",
                            "tag_key": "person3-衣裤-着装2颜色",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person3-衣裤-着装2颜色"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "婴幼儿",
                                    "value": "婴幼儿"
                                },
                                {
                                    "name": "儿童",
                                    "value": "儿童"
                                },
                                {
                                    "name": "成年",
                                    "value": "成年"
                                },
                                {
                                    "name": "老年",
                                    "value": "老年"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "fa64a825-8c41-443b-8d5e-2935b9c21dcb",
                            "tag_key": "person4-年龄",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "person4-年龄"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "男性",
                                    "value": "男性"
                                },
                                {
                                    "name": "女性",
                                    "value": "女性"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "16040035-0803-445b-aa1a-c5821e62aec7",
                            "tag_key": "person4-性别",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "person4-性别"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "b24fd09b-6684-4be3-99e7-428f05a505ce",
                            "tag_key": "person4-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person4-位置"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "阅读",
                                    "value": "阅读"
                                },
                                {
                                    "name": "化妆",
                                    "value": "化妆"
                                },
                                {
                                    "name": "吃东西",
                                    "value": "吃东西"
                                },
                                {
                                    "name": "托腮思考",
                                    "value": "托腮思考"
                                },
                                {
                                    "name": "玩手机",
                                    "value": "玩手机"
                                },
                                {
                                    "name": "打电话",
                                    "value": "打电话"
                                },
                                {
                                    "name": "吸烟",
                                    "value": "吸烟"
                                },
                                {
                                    "name": "点烟",
                                    "value": "点烟"
                                },
                                {
                                    "name": "睡觉",
                                    "value": "睡觉"
                                },
                                {
                                    "name": "抱猫",
                                    "value": "抱猫"
                                },
                                {
                                    "name": "抱狗",
                                    "value": "抱狗"
                                },
                                {
                                    "name": "头/手伸出窗外",
                                    "value": "头/手伸出窗外"
                                },
                                {
                                    "name": "哭闹",
                                    "value": "哭闹"
                                },
                                {
                                    "name": "未系安全带",
                                    "value": "未系安全带"
                                },
                                {
                                    "name": "全位置手势（食指伸出）前",
                                    "value": "全位置手势（食指伸出）前"
                                },
                                {
                                    "name": "全位置手势（食指伸出）上",
                                    "value": "全位置手势（食指伸出）上"
                                },
                                {
                                    "name": "全位置手势（食指伸出）下",
                                    "value": "全位置手势（食指伸出）下"
                                },
                                {
                                    "name": "全位置手势（食指伸出）左",
                                    "value": "全位置手势（食指伸出）左"
                                },
                                {
                                    "name": "全位置手势（食指伸出）右",
                                    "value": "全位置手势（食指伸出）右"
                                },
                                {
                                    "name": "手触碰屏幕",
                                    "value": "手触碰屏幕"
                                },
                                {
                                    "name": "站立",
                                    "value": "站立"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "4dc2e4b9-dcce-401e-a3a3-8976627fa55f",
                            "tag_key": "person4-行为",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person4-行为"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "T恤",
                                    "value": "T恤"
                                },
                                {
                                    "name": "衬衫",
                                    "value": "衬衫"
                                },
                                {
                                    "name": "毛衣",
                                    "value": "毛衣"
                                },
                                {
                                    "name": "夹克",
                                    "value": "夹克"
                                },
                                {
                                    "name": "连帽衫",
                                    "value": "连帽衫"
                                },
                                {
                                    "name": "polo衫",
                                    "value": "polo衫"
                                },
                                {
                                    "name": "西装",
                                    "value": "西装"
                                },
                                {
                                    "name": "大衣",
                                    "value": "大衣"
                                },
                                {
                                    "name": "羽绒服",
                                    "value": "羽绒服"
                                },
                                {
                                    "name": "眼镜",
                                    "value": "眼镜"
                                },
                                {
                                    "name": "围巾",
                                    "value": "围巾"
                                },
                                {
                                    "name": "帽子",
                                    "value": "帽子"
                                },
                                {
                                    "name": "耳机",
                                    "value": "耳机"
                                },
                                {
                                    "name": "手表",
                                    "value": "手表"
                                },
                                {
                                    "name": "马夹",
                                    "value": "马夹"
                                },
                                {
                                    "name": "墨镜",
                                    "value": "墨镜"
                                },
                                {
                                    "name": "口罩",
                                    "value": "口罩"
                                },
                                {
                                    "name": "连衣裙",
                                    "value": "连衣裙"
                                },
                                {
                                    "name": "背心",
                                    "value": "背心"
                                },
                                {
                                    "name": "耳坠（大）",
                                    "value": "耳坠（大）"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "0139a709-5b69-4719-b698-90cbe856e393",
                            "tag_key": "person4-衣裤-着装1类型",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person4-衣裤-着装1类型"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "灰色",
                                    "value": "灰色"
                                },
                                {
                                    "name": "红色",
                                    "value": "红色"
                                },
                                {
                                    "name": "蓝色",
                                    "value": "蓝色"
                                },
                                {
                                    "name": "橙色",
                                    "value": "橙色"
                                },
                                {
                                    "name": "黄色",
                                    "value": "黄色"
                                },
                                {
                                    "name": "绿色",
                                    "value": "绿色"
                                },
                                {
                                    "name": "紫色",
                                    "value": "紫色"
                                },
                                {
                                    "name": "黑色",
                                    "value": "黑色"
                                },
                                {
                                    "name": "白色",
                                    "value": "白色"
                                },
                                {
                                    "name": "棕色",
                                    "value": "棕色"
                                },
                                {
                                    "name": "粉色",
                                    "value": "粉色"
                                },
                                {
                                    "name": "金色",
                                    "value": "金色"
                                },
                                {
                                    "name": "银色",
                                    "value": "银色"
                                },
                                {
                                    "name": "米色",
                                    "value": "米色"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "1c0c4f42-9002-4347-bc05-11cda46b2e0b",
                            "tag_key": "person4-衣裤-着装1颜色",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person4-衣裤-着装1颜色"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "裙子",
                                    "value": "裙子"
                                },
                                {
                                    "name": "牛仔长裤",
                                    "value": "牛仔长裤"
                                },
                                {
                                    "name": "西装长裤",
                                    "value": "西装长裤"
                                },
                                {
                                    "name": "休闲长裤",
                                    "value": "休闲长裤"
                                },
                                {
                                    "name": "短裤",
                                    "value": "短裤"
                                },
                                {
                                    "name": "靴子",
                                    "value": "靴子"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "e8e915a0-a907-4b19-a3e8-3905e1c87bf6",
                            "tag_key": "person4-衣裤-着装2类型",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person4-衣裤-着装2类型"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "4",
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "灰色",
                                    "value": "灰色"
                                },
                                {
                                    "name": "红色",
                                    "value": "红色"
                                },
                                {
                                    "name": "蓝色",
                                    "value": "蓝色"
                                },
                                {
                                    "name": "橙色",
                                    "value": "橙色"
                                },
                                {
                                    "name": "黄色",
                                    "value": "黄色"
                                },
                                {
                                    "name": "绿色",
                                    "value": "绿色"
                                },
                                {
                                    "name": "紫色",
                                    "value": "紫色"
                                },
                                {
                                    "name": "黑色",
                                    "value": "黑色"
                                },
                                {
                                    "name": "白色",
                                    "value": "白色"
                                },
                                {
                                    "name": "棕色",
                                    "value": "棕色"
                                },
                                {
                                    "name": "粉色",
                                    "value": "粉色"
                                },
                                {
                                    "name": "金色",
                                    "value": "金色"
                                },
                                {
                                    "name": "银色",
                                    "value": "银色"
                                },
                                {
                                    "name": "米色",
                                    "value": "米色"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "5a546899-26e3-47c1-9024-cb89634df274",
                            "tag_key": "person4-衣裤-着装2颜色",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person4-衣裤-着装2颜色"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "婴幼儿",
                                    "value": "婴幼儿"
                                },
                                {
                                    "name": "儿童",
                                    "value": "儿童"
                                },
                                {
                                    "name": "成年",
                                    "value": "成年"
                                },
                                {
                                    "name": "老年",
                                    "value": "老年"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "2fde3e1a-8381-4315-9de5-4785c74cceae",
                            "tag_key": "person5-年龄",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "person5-年龄"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "男性",
                                    "value": "男性"
                                },
                                {
                                    "name": "女性",
                                    "value": "女性"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "b010f0f1-0bce-4f40-8a0d-dd2004bfec45",
                            "tag_key": "person5-性别",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "person5-性别"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "b3d7bc84-0969-4f4a-b0df-139b1ad86f7b",
                            "tag_key": "person5-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person5-位置"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "阅读",
                                    "value": "阅读"
                                },
                                {
                                    "name": "化妆",
                                    "value": "化妆"
                                },
                                {
                                    "name": "吃东西",
                                    "value": "吃东西"
                                },
                                {
                                    "name": "托腮思考",
                                    "value": "托腮思考"
                                },
                                {
                                    "name": "玩手机",
                                    "value": "玩手机"
                                },
                                {
                                    "name": "打电话",
                                    "value": "打电话"
                                },
                                {
                                    "name": "吸烟",
                                    "value": "吸烟"
                                },
                                {
                                    "name": "点烟",
                                    "value": "点烟"
                                },
                                {
                                    "name": "睡觉",
                                    "value": "睡觉"
                                },
                                {
                                    "name": "抱猫",
                                    "value": "抱猫"
                                },
                                {
                                    "name": "抱狗",
                                    "value": "抱狗"
                                },
                                {
                                    "name": "头/手伸出窗外",
                                    "value": "头/手伸出窗外"
                                },
                                {
                                    "name": "哭闹",
                                    "value": "哭闹"
                                },
                                {
                                    "name": "未系安全带",
                                    "value": "未系安全带"
                                },
                                {
                                    "name": "全位置手势（食指伸出）前",
                                    "value": "全位置手势（食指伸出）前"
                                },
                                {
                                    "name": "全位置手势（食指伸出）上",
                                    "value": "全位置手势（食指伸出）上"
                                },
                                {
                                    "name": "全位置手势（食指伸出）下",
                                    "value": "全位置手势（食指伸出）下"
                                },
                                {
                                    "name": "全位置手势（食指伸出）左",
                                    "value": "全位置手势（食指伸出）左"
                                },
                                {
                                    "name": "全位置手势（食指伸出）右",
                                    "value": "全位置手势（食指伸出）右"
                                },
                                {
                                    "name": "手触碰屏幕",
                                    "value": "手触碰屏幕"
                                },
                                {
                                    "name": "站立",
                                    "value": "站立"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "03d94a08-1c6c-4f84-94fd-46a91a6ea48c",
                            "tag_key": "person5-行为",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person5-行为"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "T恤",
                                    "value": "T恤"
                                },
                                {
                                    "name": "衬衫",
                                    "value": "衬衫"
                                },
                                {
                                    "name": "毛衣",
                                    "value": "毛衣"
                                },
                                {
                                    "name": "夹克",
                                    "value": "夹克"
                                },
                                {
                                    "name": "连帽衫",
                                    "value": "连帽衫"
                                },
                                {
                                    "name": "polo衫",
                                    "value": "polo衫"
                                },
                                {
                                    "name": "西装",
                                    "value": "西装"
                                },
                                {
                                    "name": "大衣",
                                    "value": "大衣"
                                },
                                {
                                    "name": "羽绒服",
                                    "value": "羽绒服"
                                },
                                {
                                    "name": "眼镜",
                                    "value": "眼镜"
                                },
                                {
                                    "name": "围巾",
                                    "value": "围巾"
                                },
                                {
                                    "name": "帽子",
                                    "value": "帽子"
                                },
                                {
                                    "name": "耳机",
                                    "value": "耳机"
                                },
                                {
                                    "name": "手表",
                                    "value": "手表"
                                },
                                {
                                    "name": "马夹",
                                    "value": "马夹"
                                },
                                {
                                    "name": "墨镜",
                                    "value": "墨镜"
                                },
                                {
                                    "name": "口罩",
                                    "value": "口罩"
                                },
                                {
                                    "name": "连衣裙",
                                    "value": "连衣裙"
                                },
                                {
                                    "name": "背心",
                                    "value": "背心"
                                },
                                {
                                    "name": "耳坠（大）",
                                    "value": "耳坠（大）"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "57d57993-15a6-4cb4-8cf8-be8e259eedf6",
                            "tag_key": "person5-衣裤-着装1类型",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person5-衣裤-着装1类型"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "灰色",
                                    "value": "灰色"
                                },
                                {
                                    "name": "红色",
                                    "value": "红色"
                                },
                                {
                                    "name": "蓝色",
                                    "value": "蓝色"
                                },
                                {
                                    "name": "橙色",
                                    "value": "橙色"
                                },
                                {
                                    "name": "黄色",
                                    "value": "黄色"
                                },
                                {
                                    "name": "绿色",
                                    "value": "绿色"
                                },
                                {
                                    "name": "紫色",
                                    "value": "紫色"
                                },
                                {
                                    "name": "黑色",
                                    "value": "黑色"
                                },
                                {
                                    "name": "白色",
                                    "value": "白色"
                                },
                                {
                                    "name": "棕色",
                                    "value": "棕色"
                                },
                                {
                                    "name": "粉色",
                                    "value": "粉色"
                                },
                                {
                                    "name": "金色",
                                    "value": "金色"
                                },
                                {
                                    "name": "银色",
                                    "value": "银色"
                                },
                                {
                                    "name": "米色",
                                    "value": "米色"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "261e967d-be78-4f12-8e46-4ffb72f21090",
                            "tag_key": "person5衣裤-着装1颜色",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person5衣裤-着装1颜色"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "裙子",
                                    "value": "裙子"
                                },
                                {
                                    "name": "牛仔长裤",
                                    "value": "牛仔长裤"
                                },
                                {
                                    "name": "西装长裤",
                                    "value": "西装长裤"
                                },
                                {
                                    "name": "休闲长裤",
                                    "value": "休闲长裤"
                                },
                                {
                                    "name": "短裤",
                                    "value": "短裤"
                                },
                                {
                                    "name": "靴子",
                                    "value": "靴子"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "faba833d-e61a-4be3-8aa9-d3a2d08bfe80",
                            "tag_key": "person5-衣裤-着装2类型",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person5-衣裤-着装2类型"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "5",
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "灰色",
                                    "value": "灰色"
                                },
                                {
                                    "name": "红色",
                                    "value": "红色"
                                },
                                {
                                    "name": "蓝色",
                                    "value": "蓝色"
                                },
                                {
                                    "name": "橙色",
                                    "value": "橙色"
                                },
                                {
                                    "name": "黄色",
                                    "value": "黄色"
                                },
                                {
                                    "name": "绿色",
                                    "value": "绿色"
                                },
                                {
                                    "name": "紫色",
                                    "value": "紫色"
                                },
                                {
                                    "name": "黑色",
                                    "value": "黑色"
                                },
                                {
                                    "name": "白色",
                                    "value": "白色"
                                },
                                {
                                    "name": "棕色",
                                    "value": "棕色"
                                },
                                {
                                    "name": "粉色",
                                    "value": "粉色"
                                },
                                {
                                    "name": "金色",
                                    "value": "金色"
                                },
                                {
                                    "name": "银色",
                                    "value": "银色"
                                },
                                {
                                    "name": "米色",
                                    "value": "米色"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "012e392c-93b9-43df-a513-6b31546b1795",
                            "tag_key": "person5-衣裤-着装2颜色",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person5-衣裤-着装2颜色"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "婴幼儿",
                                    "value": "婴幼儿"
                                },
                                {
                                    "name": "儿童",
                                    "value": "儿童"
                                },
                                {
                                    "name": "成年",
                                    "value": "成年"
                                },
                                {
                                    "name": "老年",
                                    "value": "老年"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "c70f35ee-3aac-46e1-9b48-689c926f7229",
                            "tag_key": "person6-年龄",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "person6-年龄"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "男性",
                                    "value": "男性"
                                },
                                {
                                    "name": "女性",
                                    "value": "女性"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "98b8aa46-0e06-4dc4-8158-b5056ee12764",
                            "tag_key": "person6-性别",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "person6-性别"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "918a5ecb-c94e-497d-8d9a-09cec9813f1e",
                            "tag_key": "person6-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person6-位置"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "阅读",
                                    "value": "阅读"
                                },
                                {
                                    "name": "化妆",
                                    "value": "化妆"
                                },
                                {
                                    "name": "吃东西",
                                    "value": "吃东西"
                                },
                                {
                                    "name": "托腮思考",
                                    "value": "托腮思考"
                                },
                                {
                                    "name": "玩手机",
                                    "value": "玩手机"
                                },
                                {
                                    "name": "打电话",
                                    "value": "打电话"
                                },
                                {
                                    "name": "吸烟",
                                    "value": "吸烟"
                                },
                                {
                                    "name": "点烟",
                                    "value": "点烟"
                                },
                                {
                                    "name": "睡觉",
                                    "value": "睡觉"
                                },
                                {
                                    "name": "抱猫",
                                    "value": "抱猫"
                                },
                                {
                                    "name": "抱狗",
                                    "value": "抱狗"
                                },
                                {
                                    "name": "头/手伸出窗外",
                                    "value": "头/手伸出窗外"
                                },
                                {
                                    "name": "哭闹",
                                    "value": "哭闹"
                                },
                                {
                                    "name": "未系安全带",
                                    "value": "未系安全带"
                                },
                                {
                                    "name": "全位置手势（食指伸出）前",
                                    "value": "全位置手势（食指伸出）前"
                                },
                                {
                                    "name": "全位置手势（食指伸出）上",
                                    "value": "全位置手势（食指伸出）上"
                                },
                                {
                                    "name": "全位置手势（食指伸出）下",
                                    "value": "全位置手势（食指伸出）下"
                                },
                                {
                                    "name": "全位置手势（食指伸出）左",
                                    "value": "全位置手势（食指伸出）左"
                                },
                                {
                                    "name": "全位置手势（食指伸出）右",
                                    "value": "全位置手势（食指伸出）右"
                                },
                                {
                                    "name": "手触碰屏幕",
                                    "value": "手触碰屏幕"
                                },
                                {
                                    "name": "站立",
                                    "value": "站立"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "3e36477a-b630-4a37-9fa8-70857a1bfb05",
                            "tag_key": "person6-行为",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person6-行为"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "T恤",
                                    "value": "T恤"
                                },
                                {
                                    "name": "衬衫",
                                    "value": "衬衫"
                                },
                                {
                                    "name": "毛衣",
                                    "value": "毛衣"
                                },
                                {
                                    "name": "夹克",
                                    "value": "夹克"
                                },
                                {
                                    "name": "连帽衫",
                                    "value": "连帽衫"
                                },
                                {
                                    "name": "polo衫",
                                    "value": "polo衫"
                                },
                                {
                                    "name": "西装",
                                    "value": "西装"
                                },
                                {
                                    "name": "大衣",
                                    "value": "大衣"
                                },
                                {
                                    "name": "羽绒服",
                                    "value": "羽绒服"
                                },
                                {
                                    "name": "眼镜",
                                    "value": "眼镜"
                                },
                                {
                                    "name": "围巾",
                                    "value": "围巾"
                                },
                                {
                                    "name": "帽子",
                                    "value": "帽子"
                                },
                                {
                                    "name": "耳机",
                                    "value": "耳机"
                                },
                                {
                                    "name": "手表",
                                    "value": "手表"
                                },
                                {
                                    "name": "马夹",
                                    "value": "马夹"
                                },
                                {
                                    "name": "墨镜",
                                    "value": "墨镜"
                                },
                                {
                                    "name": "口罩",
                                    "value": "口罩"
                                },
                                {
                                    "name": "连衣裙",
                                    "value": "连衣裙"
                                },
                                {
                                    "name": "背心",
                                    "value": "背心"
                                },
                                {
                                    "name": "耳坠（大）",
                                    "value": "耳坠（大）"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "33166d31-5658-4c0e-aea8-c4788a56929d",
                            "tag_key": "person6-衣裤-着装1类型",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person6-衣裤-着装1类型"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "灰色",
                                    "value": "灰色"
                                },
                                {
                                    "name": "红色",
                                    "value": "红色"
                                },
                                {
                                    "name": "蓝色",
                                    "value": "蓝色"
                                },
                                {
                                    "name": "橙色",
                                    "value": "橙色"
                                },
                                {
                                    "name": "黄色",
                                    "value": "黄色"
                                },
                                {
                                    "name": "绿色",
                                    "value": "绿色"
                                },
                                {
                                    "name": "紫色",
                                    "value": "紫色"
                                },
                                {
                                    "name": "黑色",
                                    "value": "黑色"
                                },
                                {
                                    "name": "白色",
                                    "value": "白色"
                                },
                                {
                                    "name": "棕色",
                                    "value": "棕色"
                                },
                                {
                                    "name": "粉色",
                                    "value": "粉色"
                                },
                                {
                                    "name": "金色",
                                    "value": "金色"
                                },
                                {
                                    "name": "银色",
                                    "value": "银色"
                                },
                                {
                                    "name": "米色",
                                    "value": "米色"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "60f44d21-b54e-423c-9df8-19744d59bd82",
                            "tag_key": "person6-衣裤-着装1颜色",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person6-衣裤-着装1颜色"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "裙子",
                                    "value": "裙子"
                                },
                                {
                                    "name": "牛仔长裤",
                                    "value": "牛仔长裤"
                                },
                                {
                                    "name": "西装长裤",
                                    "value": "西装长裤"
                                },
                                {
                                    "name": "休闲长裤",
                                    "value": "休闲长裤"
                                },
                                {
                                    "name": "短裤",
                                    "value": "短裤"
                                },
                                {
                                    "name": "靴子",
                                    "value": "靴子"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "3c256e5a-c6fe-44e6-9e37-ae5f5448618d",
                            "tag_key": "person6-衣裤-着装2类型",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person6-衣裤-着装2类型"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "4c7c41cd-ff3c-48f9-89ff-b714058aa91e",
                                "depends_value": [
                                    "6"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "灰色",
                                    "value": "灰色"
                                },
                                {
                                    "name": "红色",
                                    "value": "红色"
                                },
                                {
                                    "name": "蓝色",
                                    "value": "蓝色"
                                },
                                {
                                    "name": "橙色",
                                    "value": "橙色"
                                },
                                {
                                    "name": "黄色",
                                    "value": "黄色"
                                },
                                {
                                    "name": "绿色",
                                    "value": "绿色"
                                },
                                {
                                    "name": "紫色",
                                    "value": "紫色"
                                },
                                {
                                    "name": "黑色",
                                    "value": "黑色"
                                },
                                {
                                    "name": "白色",
                                    "value": "白色"
                                },
                                {
                                    "name": "棕色",
                                    "value": "棕色"
                                },
                                {
                                    "name": "粉色",
                                    "value": "粉色"
                                },
                                {
                                    "name": "金色",
                                    "value": "金色"
                                },
                                {
                                    "name": "银色",
                                    "value": "银色"
                                },
                                {
                                    "name": "米色",
                                    "value": "米色"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "8e19afb5-6cfe-42e6-92bd-502a54268ee2",
                            "tag_key": "person6-衣裤-着装2颜色",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "person6-衣裤-着装2颜色"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                                "depends_value": [
                                    "1",
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6",
                                    "7"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    },
                                    {
                                        "label": "7",
                                        "value": "7"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "背包",
                                    "value": "背包"
                                },
                                {
                                    "name": "宠物包",
                                    "value": "宠物包"
                                },
                                {
                                    "name": "笔记本",
                                    "value": "笔记本"
                                },
                                {
                                    "name": "手机",
                                    "value": "手机"
                                },
                                {
                                    "name": "平板",
                                    "value": "平板"
                                },
                                {
                                    "name": "挎包(单肩包、手袋)",
                                    "value": "挎包(单肩包、手袋)"
                                },
                                {
                                    "name": "水杯",
                                    "value": "水杯"
                                },
                                {
                                    "name": "易拉罐",
                                    "value": "易拉罐"
                                },
                                {
                                    "name": "保温杯",
                                    "value": "保温杯"
                                },
                                {
                                    "name": "大型行李箱",
                                    "value": "大型行李箱"
                                },
                                {
                                    "name": "大纸箱",
                                    "value": "大纸箱"
                                },
                                {
                                    "name": "玩偶",
                                    "value": "玩偶"
                                },
                                {
                                    "name": "衣服（除外套）",
                                    "value": "衣服（除外套）"
                                },
                                {
                                    "name": "外套",
                                    "value": "外套"
                                },
                                {
                                    "name": "钱包",
                                    "value": "钱包"
                                },
                                {
                                    "name": "书本",
                                    "value": "书本"
                                },
                                {
                                    "name": "鲜花",
                                    "value": "鲜花"
                                },
                                {
                                    "name": "抱枕",
                                    "value": "抱枕"
                                },
                                {
                                    "name": "口罩",
                                    "value": "口罩"
                                },
                                {
                                    "name": "帽子",
                                    "value": "帽子"
                                },
                                {
                                    "name": "纸巾盒",
                                    "value": "纸巾盒"
                                },
                                {
                                    "name": "钥匙",
                                    "value": "钥匙"
                                },
                                {
                                    "name": "瓶装酒水",
                                    "value": "瓶装酒水"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "空白",
                                    "value": "空白"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "b81caf79-a518-4a6d-8249-94142457feca",
                            "tag_key": "good1-种类",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "good1-种类"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                                "depends_value": [
                                    "1",
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6",
                                    "7"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    },
                                    {
                                        "label": "7",
                                        "value": "7"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "前排扶手箱",
                                    "value": "前排扶手箱"
                                },
                                {
                                    "name": "前排扶手箱-杯槽",
                                    "value": "前排扶手箱-杯槽"
                                },
                                {
                                    "name": "后排扶手箱",
                                    "value": "后排扶手箱"
                                },
                                {
                                    "name": "后排扶手箱-杯槽",
                                    "value": "后排扶手箱-杯槽"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "78eb1147-648d-49ee-a2cb-69d18b003288",
                            "tag_key": "good1-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "good1-位置"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                                "depends_value": [
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6",
                                    "7"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    },
                                    {
                                        "label": "7",
                                        "value": "7"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "背包",
                                    "value": "背包"
                                },
                                {
                                    "name": "宠物包",
                                    "value": "宠物包"
                                },
                                {
                                    "name": "笔记本",
                                    "value": "笔记本"
                                },
                                {
                                    "name": "手机",
                                    "value": "手机"
                                },
                                {
                                    "name": "平板",
                                    "value": "平板"
                                },
                                {
                                    "name": "挎包(单肩包、手袋)",
                                    "value": "挎包(单肩包、手袋)"
                                },
                                {
                                    "name": "水杯",
                                    "value": "水杯"
                                },
                                {
                                    "name": "易拉罐",
                                    "value": "易拉罐"
                                },
                                {
                                    "name": "保温杯",
                                    "value": "保温杯"
                                },
                                {
                                    "name": "大型行李箱",
                                    "value": "大型行李箱"
                                },
                                {
                                    "name": "大纸箱",
                                    "value": "大纸箱"
                                },
                                {
                                    "name": "玩偶",
                                    "value": "玩偶"
                                },
                                {
                                    "name": "衣服（除外套）",
                                    "value": "衣服（除外套）"
                                },
                                {
                                    "name": "外套",
                                    "value": "外套"
                                },
                                {
                                    "name": "钱包",
                                    "value": "钱包"
                                },
                                {
                                    "name": "书本",
                                    "value": "书本"
                                },
                                {
                                    "name": "鲜花",
                                    "value": "鲜花"
                                },
                                {
                                    "name": "抱枕",
                                    "value": "抱枕"
                                },
                                {
                                    "name": "口罩",
                                    "value": "口罩"
                                },
                                {
                                    "name": "帽子",
                                    "value": "帽子"
                                },
                                {
                                    "name": "纸巾盒",
                                    "value": "纸巾盒"
                                },
                                {
                                    "name": "钥匙",
                                    "value": "钥匙"
                                },
                                {
                                    "name": "瓶装酒水",
                                    "value": "瓶装酒水"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "空白",
                                    "value": "空白"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "dcfed6ee-ea9e-41b1-b59c-34d6f5af20c5",
                            "tag_key": "good2-种类",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "good2-种类"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                                "depends_value": [
                                    "2",
                                    "3",
                                    "4",
                                    "5",
                                    "6",
                                    "7"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    },
                                    {
                                        "label": "7",
                                        "value": "7"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "前排扶手箱",
                                    "value": "前排扶手箱"
                                },
                                {
                                    "name": "前排扶手箱-杯槽",
                                    "value": "前排扶手箱-杯槽"
                                },
                                {
                                    "name": "后排扶手箱",
                                    "value": "后排扶手箱"
                                },
                                {
                                    "name": "后排扶手箱-杯槽",
                                    "value": "后排扶手箱-杯槽"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "2b424eaa-d383-41f4-bf01-d833757d4d08",
                            "tag_key": "good2-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "good2-位置"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                                "depends_value": [
                                    "3",
                                    "4",
                                    "5",
                                    "6",
                                    "7"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    },
                                    {
                                        "label": "7",
                                        "value": "7"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "背包",
                                    "value": "背包"
                                },
                                {
                                    "name": "宠物包",
                                    "value": "宠物包"
                                },
                                {
                                    "name": "笔记本",
                                    "value": "笔记本"
                                },
                                {
                                    "name": "手机",
                                    "value": "手机"
                                },
                                {
                                    "name": "平板",
                                    "value": "平板"
                                },
                                {
                                    "name": "挎包(单肩包、手袋)",
                                    "value": "挎包(单肩包、手袋)"
                                },
                                {
                                    "name": "水杯",
                                    "value": "水杯"
                                },
                                {
                                    "name": "易拉罐",
                                    "value": "易拉罐"
                                },
                                {
                                    "name": "保温杯",
                                    "value": "保温杯"
                                },
                                {
                                    "name": "大型行李箱",
                                    "value": "大型行李箱"
                                },
                                {
                                    "name": "大纸箱",
                                    "value": "大纸箱"
                                },
                                {
                                    "name": "玩偶",
                                    "value": "玩偶"
                                },
                                {
                                    "name": "衣服（除外套）",
                                    "value": "衣服（除外套）"
                                },
                                {
                                    "name": "外套",
                                    "value": "外套"
                                },
                                {
                                    "name": "钱包",
                                    "value": "钱包"
                                },
                                {
                                    "name": "书本",
                                    "value": "书本"
                                },
                                {
                                    "name": "鲜花",
                                    "value": "鲜花"
                                },
                                {
                                    "name": "抱枕",
                                    "value": "抱枕"
                                },
                                {
                                    "name": "口罩",
                                    "value": "口罩"
                                },
                                {
                                    "name": "帽子",
                                    "value": "帽子"
                                },
                                {
                                    "name": "纸巾盒",
                                    "value": "纸巾盒"
                                },
                                {
                                    "name": "钥匙",
                                    "value": "钥匙"
                                },
                                {
                                    "name": "瓶装酒水",
                                    "value": "瓶装酒水"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "空白",
                                    "value": "空白"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "6eeaae4a-520e-459a-9f6d-fb1125f92e50",
                            "tag_key": "good3-种类",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "good3-种类"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                                "depends_value": [
                                    "3",
                                    "4",
                                    "5",
                                    "6",
                                    "7"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    },
                                    {
                                        "label": "7",
                                        "value": "7"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "前排扶手箱",
                                    "value": "前排扶手箱"
                                },
                                {
                                    "name": "前排扶手箱-杯槽",
                                    "value": "前排扶手箱-杯槽"
                                },
                                {
                                    "name": "后排扶手箱",
                                    "value": "后排扶手箱"
                                },
                                {
                                    "name": "后排扶手箱-杯槽",
                                    "value": "后排扶手箱-杯槽"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "dceb873f-b4b0-4d0b-b2b6-e77aea3c030a",
                            "tag_key": "good3-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "good3-位置"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                                "depends_value": [
                                    "4",
                                    "5",
                                    "6",
                                    "7"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    },
                                    {
                                        "label": "7",
                                        "value": "7"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "背包",
                                    "value": "背包"
                                },
                                {
                                    "name": "宠物包",
                                    "value": "宠物包"
                                },
                                {
                                    "name": "笔记本",
                                    "value": "笔记本"
                                },
                                {
                                    "name": "手机",
                                    "value": "手机"
                                },
                                {
                                    "name": "平板",
                                    "value": "平板"
                                },
                                {
                                    "name": "挎包(单肩包、手袋)",
                                    "value": "挎包(单肩包、手袋)"
                                },
                                {
                                    "name": "水杯",
                                    "value": "水杯"
                                },
                                {
                                    "name": "易拉罐",
                                    "value": "易拉罐"
                                },
                                {
                                    "name": "保温杯",
                                    "value": "保温杯"
                                },
                                {
                                    "name": "大型行李箱",
                                    "value": "大型行李箱"
                                },
                                {
                                    "name": "大纸箱",
                                    "value": "大纸箱"
                                },
                                {
                                    "name": "玩偶",
                                    "value": "玩偶"
                                },
                                {
                                    "name": "衣服（除外套）",
                                    "value": "衣服（除外套）"
                                },
                                {
                                    "name": "外套",
                                    "value": "外套"
                                },
                                {
                                    "name": "钱包",
                                    "value": "钱包"
                                },
                                {
                                    "name": "书本",
                                    "value": "书本"
                                },
                                {
                                    "name": "鲜花",
                                    "value": "鲜花"
                                },
                                {
                                    "name": "抱枕",
                                    "value": "抱枕"
                                },
                                {
                                    "name": "口罩",
                                    "value": "口罩"
                                },
                                {
                                    "name": "帽子",
                                    "value": "帽子"
                                },
                                {
                                    "name": "纸巾盒",
                                    "value": "纸巾盒"
                                },
                                {
                                    "name": "钥匙",
                                    "value": "钥匙"
                                },
                                {
                                    "name": "瓶装酒水",
                                    "value": "瓶装酒水"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "空白",
                                    "value": "空白"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "1e62f844-7e64-4271-bbe5-c9227b6ed210",
                            "tag_key": "good4-种类",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "good4-种类"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                                "depends_value": [
                                    "4",
                                    "5",
                                    "6",
                                    "7"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    },
                                    {
                                        "label": "7",
                                        "value": "7"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "前排扶手箱",
                                    "value": "前排扶手箱"
                                },
                                {
                                    "name": "前排扶手箱-杯槽",
                                    "value": "前排扶手箱-杯槽"
                                },
                                {
                                    "name": "后排扶手箱",
                                    "value": "后排扶手箱"
                                },
                                {
                                    "name": "后排扶手箱-杯槽",
                                    "value": "后排扶手箱-杯槽"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "2dde84c5-aa9e-4a09-b483-5096b1d48908",
                            "tag_key": "good4-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "good4-位置"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                                "depends_value": [
                                    "5",
                                    "6",
                                    "7"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    },
                                    {
                                        "label": "7",
                                        "value": "7"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "背包",
                                    "value": "背包"
                                },
                                {
                                    "name": "宠物包",
                                    "value": "宠物包"
                                },
                                {
                                    "name": "笔记本",
                                    "value": "笔记本"
                                },
                                {
                                    "name": "手机",
                                    "value": "手机"
                                },
                                {
                                    "name": "平板",
                                    "value": "平板"
                                },
                                {
                                    "name": "挎包(单肩包、手袋)",
                                    "value": "挎包(单肩包、手袋)"
                                },
                                {
                                    "name": "水杯",
                                    "value": "水杯"
                                },
                                {
                                    "name": "易拉罐",
                                    "value": "易拉罐"
                                },
                                {
                                    "name": "保温杯",
                                    "value": "保温杯"
                                },
                                {
                                    "name": "大型行李箱",
                                    "value": "大型行李箱"
                                },
                                {
                                    "name": "大纸箱",
                                    "value": "大纸箱"
                                },
                                {
                                    "name": "玩偶",
                                    "value": "玩偶"
                                },
                                {
                                    "name": "衣服（除外套）",
                                    "value": "衣服（除外套）"
                                },
                                {
                                    "name": "外套",
                                    "value": "外套"
                                },
                                {
                                    "name": "钱包",
                                    "value": "钱包"
                                },
                                {
                                    "name": "书本",
                                    "value": "书本"
                                },
                                {
                                    "name": "鲜花",
                                    "value": "鲜花"
                                },
                                {
                                    "name": "抱枕",
                                    "value": "抱枕"
                                },
                                {
                                    "name": "口罩",
                                    "value": "口罩"
                                },
                                {
                                    "name": "帽子",
                                    "value": "帽子"
                                },
                                {
                                    "name": "纸巾盒",
                                    "value": "纸巾盒"
                                },
                                {
                                    "name": "钥匙",
                                    "value": "钥匙"
                                },
                                {
                                    "name": "瓶装酒水",
                                    "value": "瓶装酒水"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "空白",
                                    "value": "空白"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "bf8f800f-013c-4a93-9675-2f0e1bb5c044",
                            "tag_key": "good5-种类",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "good5-种类"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                                "depends_value": [
                                    "5",
                                    "6",
                                    "7"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    },
                                    {
                                        "label": "7",
                                        "value": "7"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "前排扶手箱",
                                    "value": "前排扶手箱"
                                },
                                {
                                    "name": "前排扶手箱-杯槽",
                                    "value": "前排扶手箱-杯槽"
                                },
                                {
                                    "name": "后排扶手箱",
                                    "value": "后排扶手箱"
                                },
                                {
                                    "name": "后排扶手箱-杯槽",
                                    "value": "后排扶手箱-杯槽"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "81b23249-a0a3-412f-af72-afc563ed1ab7",
                            "tag_key": "good5-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "good5-位置"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                                "depends_value": [
                                    "6",
                                    "7"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    },
                                    {
                                        "label": "7",
                                        "value": "7"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "背包",
                                    "value": "背包"
                                },
                                {
                                    "name": "宠物包",
                                    "value": "宠物包"
                                },
                                {
                                    "name": "笔记本",
                                    "value": "笔记本"
                                },
                                {
                                    "name": "手机",
                                    "value": "手机"
                                },
                                {
                                    "name": "平板",
                                    "value": "平板"
                                },
                                {
                                    "name": "挎包(单肩包、手袋)",
                                    "value": "挎包(单肩包、手袋)"
                                },
                                {
                                    "name": "水杯",
                                    "value": "水杯"
                                },
                                {
                                    "name": "易拉罐",
                                    "value": "易拉罐"
                                },
                                {
                                    "name": "保温杯",
                                    "value": "保温杯"
                                },
                                {
                                    "name": "大型行李箱",
                                    "value": "大型行李箱"
                                },
                                {
                                    "name": "大纸箱",
                                    "value": "大纸箱"
                                },
                                {
                                    "name": "玩偶",
                                    "value": "玩偶"
                                },
                                {
                                    "name": "衣服（除外套）",
                                    "value": "衣服（除外套）"
                                },
                                {
                                    "name": "外套",
                                    "value": "外套"
                                },
                                {
                                    "name": "钱包",
                                    "value": "钱包"
                                },
                                {
                                    "name": "书本",
                                    "value": "书本"
                                },
                                {
                                    "name": "鲜花",
                                    "value": "鲜花"
                                },
                                {
                                    "name": "抱枕",
                                    "value": "抱枕"
                                },
                                {
                                    "name": "口罩",
                                    "value": "口罩"
                                },
                                {
                                    "name": "帽子",
                                    "value": "帽子"
                                },
                                {
                                    "name": "纸巾盒",
                                    "value": "纸巾盒"
                                },
                                {
                                    "name": "钥匙",
                                    "value": "钥匙"
                                },
                                {
                                    "name": "瓶装酒水",
                                    "value": "瓶装酒水"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "空白",
                                    "value": "空白"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "f448371d-2684-438f-b702-460571e6d889",
                            "tag_key": "good6-种类",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "good6-种类"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                                "depends_value": [
                                    "6",
                                    "7"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    },
                                    {
                                        "label": "7",
                                        "value": "7"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "前排扶手箱",
                                    "value": "前排扶手箱"
                                },
                                {
                                    "name": "前排扶手箱-杯槽",
                                    "value": "前排扶手箱-杯槽"
                                },
                                {
                                    "name": "后排扶手箱",
                                    "value": "后排扶手箱"
                                },
                                {
                                    "name": "后排扶手箱-杯槽",
                                    "value": "后排扶手箱-杯槽"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "a2ade63e-e672-46cd-aa95-67973ca46f34",
                            "tag_key": "good6-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "good6-位置"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                                "depends_value": [
                                    "7"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    },
                                    {
                                        "label": "7",
                                        "value": "7"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "背包",
                                    "value": "背包"
                                },
                                {
                                    "name": "宠物包",
                                    "value": "宠物包"
                                },
                                {
                                    "name": "笔记本",
                                    "value": "笔记本"
                                },
                                {
                                    "name": "手机",
                                    "value": "手机"
                                },
                                {
                                    "name": "平板",
                                    "value": "平板"
                                },
                                {
                                    "name": "挎包(单肩包、手袋)",
                                    "value": "挎包(单肩包、手袋)"
                                },
                                {
                                    "name": "水杯",
                                    "value": "水杯"
                                },
                                {
                                    "name": "易拉罐",
                                    "value": "易拉罐"
                                },
                                {
                                    "name": "保温杯",
                                    "value": "保温杯"
                                },
                                {
                                    "name": "大型行李箱",
                                    "value": "大型行李箱"
                                },
                                {
                                    "name": "大纸箱",
                                    "value": "大纸箱"
                                },
                                {
                                    "name": "玩偶",
                                    "value": "玩偶"
                                },
                                {
                                    "name": "衣服（除外套）",
                                    "value": "衣服（除外套）"
                                },
                                {
                                    "name": "外套",
                                    "value": "外套"
                                },
                                {
                                    "name": "钱包",
                                    "value": "钱包"
                                },
                                {
                                    "name": "书本",
                                    "value": "书本"
                                },
                                {
                                    "name": "鲜花",
                                    "value": "鲜花"
                                },
                                {
                                    "name": "抱枕",
                                    "value": "抱枕"
                                },
                                {
                                    "name": "口罩",
                                    "value": "口罩"
                                },
                                {
                                    "name": "帽子",
                                    "value": "帽子"
                                },
                                {
                                    "name": "纸巾盒",
                                    "value": "纸巾盒"
                                },
                                {
                                    "name": "钥匙",
                                    "value": "钥匙"
                                },
                                {
                                    "name": "瓶装酒水",
                                    "value": "瓶装酒水"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "空白",
                                    "value": "空白"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "a3431fa4-5ad1-445f-b80c-f523f398fa27",
                            "tag_key": "good7-种类",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "good7-种类"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "2b3244b5-a289-4d0a-b482-9af1f9d78ad4",
                                "depends_value": [
                                    "7"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    },
                                    {
                                        "label": "3",
                                        "value": "3"
                                    },
                                    {
                                        "label": "4",
                                        "value": "4"
                                    },
                                    {
                                        "label": "5",
                                        "value": "5"
                                    },
                                    {
                                        "label": "6",
                                        "value": "6"
                                    },
                                    {
                                        "label": "7",
                                        "value": "7"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "前排扶手箱",
                                    "value": "前排扶手箱"
                                },
                                {
                                    "name": "前排扶手箱-杯槽",
                                    "value": "前排扶手箱-杯槽"
                                },
                                {
                                    "name": "后排扶手箱",
                                    "value": "后排扶手箱"
                                },
                                {
                                    "name": "后排扶手箱-杯槽",
                                    "value": "后排扶手箱-杯槽"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "cd63baf9-89b6-4e1d-b6f9-0cffb6aa156c",
                            "tag_key": "good7-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "good7-位置"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "410f81f1-edb3-46bb-82da-2ce866aff978",
                                "depends_value": [
                                    "1",
                                    "2"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "猫",
                                    "value": "猫"
                                },
                                {
                                    "name": "狗",
                                    "value": "狗"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "空白",
                                    "value": "空白"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "1679f1b0-d5f4-4b3f-a09e-43feed51b03b",
                            "tag_key": "pet1-种类",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "pet1-种类"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "410f81f1-edb3-46bb-82da-2ce866aff978",
                                "depends_value": [
                                    "1",
                                    "2"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "前排扶手箱",
                                    "value": "前排扶手箱"
                                },
                                {
                                    "name": "后排扶手箱",
                                    "value": "后排扶手箱"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "2cc1ddcb-f2ff-4393-baca-6e3b2a4ccbe8",
                            "tag_key": "pet1-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "pet1-位置"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "410f81f1-edb3-46bb-82da-2ce866aff978",
                                "depends_value": [
                                    "2"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "猫",
                                    "value": "猫"
                                },
                                {
                                    "name": "狗",
                                    "value": "狗"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                },
                                {
                                    "name": "空白",
                                    "value": "空白"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "0fb3911f-b49a-4700-8c18-fcbc6815247e",
                            "tag_key": "pet2-种类",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "pet2-种类"
                        },
                        {
                            "default_value": [],
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "410f81f1-edb3-46bb-82da-2ce866aff978",
                                "depends_value": [
                                    "2"
                                ],
                                "option": [
                                    {
                                        "label": "0",
                                        "value": "0"
                                    },
                                    {
                                        "label": "1",
                                        "value": "1"
                                    },
                                    {
                                        "label": "2",
                                        "value": "2"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "主驾",
                                    "value": "主驾"
                                },
                                {
                                    "name": "副驾",
                                    "value": "副驾"
                                },
                                {
                                    "name": "二排左",
                                    "value": "二排左"
                                },
                                {
                                    "name": "二排中",
                                    "value": "二排中"
                                },
                                {
                                    "name": "二排右",
                                    "value": "二排右"
                                },
                                {
                                    "name": "三排左",
                                    "value": "三排左"
                                },
                                {
                                    "name": "三排右",
                                    "value": "三排右"
                                },
                                {
                                    "name": "前排扶手箱",
                                    "value": "前排扶手箱"
                                },
                                {
                                    "name": "后排扶手箱",
                                    "value": "后排扶手箱"
                                },
                                {
                                    "name": "过道",
                                    "value": "过道"
                                },
                                {
                                    "name": "UNKNOWN",
                                    "value": "UNKNOWN"
                                }
                            ],
                            "is_global": "true",
                            "order": 1,
                            "required": "true",
                            "tag_id": "5d60bf51-6677-42dd-8abf-1cf3fff7389b",
                            "tag_key": "pet2-位置",
                            "tag_type": "multiple",
                            "value": [],
                            "view_name": "pet2-位置"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "depends": {
                                "depends_on": "dc17a1fd-6fab-42e7-b15d-abdfc1a74910",
                                "depends_value": [
                                    "可用"
                                ],
                                "option": [
                                    {
                                        "label": "抛弃",
                                        "value": "抛弃"
                                    },
                                    {
                                        "label": "可用",
                                        "value": "可用"
                                    }
                                ]
                            },
                            "display": "true",
                            "enum_list": [
                                {
                                    "name": "一排",
                                    "value": "一排"
                                },
                                {
                                    "name": "二排",
                                    "value": "二排"
                                }
                            ],
                            "is_global": "false",
                            "order": 1,
                            "required": "true",
                            "tag_id": "23775417-4da1-424c-9acd-343f899d6789",
                            "tag_key": "摄像头位置",
                            "tag_type": "single",
                            "value": "",
                            "view_name": "摄像头位置"
                        },
                        {
                            "default_value": "",
                            "default_value_option": "no",
                            "display": "true",
                            "is_global": "true",
                            "order": 1,
                            "required": "false",
                            "tag_id": "4bc35a32-9453-473f-aa0a-5b645765e5f5",
                            "tag_key": "整体备注",
                            "tag_type": "text_box",
                            "value": "",
                            "view_name": "整体备注"
                        }
                    ]
                }
            ]
        },
        "specific": {
            "100000": []
        }
    }
}






    final_result = fill_standard_input(data_to_embed, standardInput_template)

    # 以美化的格式打印最终生成的完整JSON
    with open("outputs/test20.json", "w", encoding="utf-8") as f:
        json.dump(final_result, f, ensure_ascii=False, indent=4)
    # print(json.dumps(final_result, indent=4, ensure_ascii=False))