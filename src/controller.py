import flatdict
import inspect
import json
import tempfile
import os

from flask import make_response, url_for
from psd_tools import PSDImage
from psd_tools.api.layers import Artboard
from psd_tools.api.effects import Stroke, DropShadow


class Translate_controller():
    def __init__(self):
        pass

    
    def get_layer_effects_info(self, layer):
        effects_info = []
        for effect in layer.effects:
            if isinstance(effect, Stroke):
                stroke_info = {
                    'type': 'Stroke',
                    'color': effect.color,
                    'size': effect.size,
                    'opacity': effect.opacity

                }
                effects_info.append(stroke_info)
            elif isinstance(effect, DropShadow):
                shadow_info = {
                    'type': 'Drop Shadow',
                    'color': effect.color,
                    'size': effect.size,
                    'opacity': effect.opacity,
                    'angle': effect.angle,
                    'distance': effect.distance
                }
                effects_info.append(shadow_info)
            else:
                info = {
                    'type': 'Other',
                    'color': effect.color,
                    'size': effect.size
                }
                effects_info.append(info)

        return effects_info
    

    def export_sub_layer_as_png(self, sub_layer, sub_layer_info):
        if sub_layer_info['kind'] != 'type':
            filename = 'output_file.png'
            # sub_layer is the info, and this saves as png
            output = sub_layer.composite().convert('RGB').save(filename)


    def get_artboard_info(self, psd):
        artboard_info = []
        try:
            for layer_order, layer in enumerate(psd):
                if isinstance(layer, Artboard):
                    artboard_name = layer.name
                    artboard_layers = []  
                    for sub_layer_order, sub_layer in enumerate(layer):
                        top_left_x, top_left_y, bottom_right_x, bottom_right_y = sub_layer.bbox
                        width = bottom_right_x - top_left_x
                        height = bottom_right_y - top_left_y
                        sub_layer_info = {
                            'name': sub_layer.name,
                            'x': top_left_x,
                            'y': top_left_y,
                            'width': width,
                            'height': height,
                            'kind': sub_layer.kind,
                            'order': sub_layer_order,
                            'blend_mode': sub_layer.blend_mode,
                        }
                        if sub_layer.kind == 'type':
                            sub_layer_info.update({
                                'opacity': sub_layer.opacity,
                                'font_list': sub_layer.resource_dict.get('FontSet', []),
                                'style_sheet': sub_layer.engine_dict.get('StyleRun', []),
                            })
                        artboard_layers.append({
                            'info': sub_layer_info,  
                            'layer': sub_layer
                        })
                    artboard_info.append({
                        'name': artboard_name,
                        'layers': artboard_layers,
                        'artboard': layer
                    })
        except Exception as e:
            print(f'Exception: {repr(e)}')
            return None
        return artboard_info        


    def parse_artboards(self, artboard_info):
        data = []
        for info in artboard_info:
            data.append(info)
            for entry in info['layers']:
                sub_layer_info = entry['info'] 
                sub_layer = entry['layer']  # PSD layer object
                # Export sub-layer as PNG
                print('HEJHKJSDFH')
                print(sub_layer_info)
                # self.export_sub_layer_as_png(sub_layer, sub_layer_info)

        return data


    def extract_parts_from_group(self, group, output_dir, group_order):
        group_info = []
        for i, layer in enumerate(group):
            if layer.is_visible():
                group_order += 1
                if layer.is_group():
                    subgroup_info, group_order = self.extract_parts_from_group(layer, output_dir, group_order)
                    group_info.extend(subgroup_info)
                else:
                    blending_mode = layer.blend_mode
                    if layer.kind == 'type':
                        text_info = {
                            'name': f'{group.name}_part_{i}',
                            'bbox': layer.bbox,
                            'kind': layer.kind,
                            'text': layer.text,
                            'order': group_order,  # Add group order
                            'style_sheet': layer.engine_dict.get('StyleRun', ['RunArray']),
                            'font_list': layer.resource_dict.get('FontSet', []),
                            'blend_mode': blending_mode,  # Add blending mode
                            'opacity': layer.opacity,  # Add opacity
                        }
                        group_info.append(text_info)

                    img = layer.composite()
                    img.convert('RGB').save(os.path.join(output_dir, f'{group.name}_part_{i}.png'))

        return group_info, group_order
    

    def separate_parts(self, psd):
        output_dir = tempfile.mkdtemp()
        layer_info = [] 
        layer_order = 0 

        for layer in psd:
            if layer.is_visible():
                layer_order += 1 
                if layer.is_group():
                    group_info, group_order = self.extract_parts_from_group(layer, output_dir, layer_order)
                    layer_info.extend(group_info)
                    layer_order = group_order 
                else:
                    blending_mode = layer.blend_mode
                    if layer.kind == 'type':
                        # Skip exporting type layers
                        text_info = {
                            'name': layer.name,
                            'kind': layer.kind,
                            'text': layer.text,
                            'blend_mode': blending_mode,  # Add blending mode
                            'opacity': layer.opacity,  # Add opacity
                            'style_sheet': layer.engine_dict.get('StyleRun', []),
                            'font_list': layer.resource_dict.get('FontSet', [])
                        }
                        layer_info.append(text_info)
                    else:
                        # Export all other layers as PNG
                        img = layer.composite()
                        img.convert('RGB').save(os.path.join(output_dir, f'{layer.name}.png'))

        return output_dir, layer_info, psd.width, psd.height


    def parse_non_text_layer(self, layer):
        output = {}
        
        if layer.kind == 'pixel':
            output = {
                'name': layer.name,
                'kind': layer.kind,
                'bbox': str(layer.bbox),
                'width': layer.width,
                'height': layer.height,
                'opacity': layer.opacity,
                'blend_mode': str(layer.blend_mode).replace('Blend', '')
            }
        elif layer.kind == 'shape':
            shapes = []
            for shape in layer.origination:
                shapes.append(shape)
            output = {
                'name': layer.name,
                'kind': layer.kind,
                'bbox': str(layer.bbox),
                'opacity': layer.opacity,
                'shapes': str(shapes),
                'vector_mask': str(layer.vector_mask)
            }
        return output


    def parse_text_layer(self, layer):
        output = {
            'name': layer.name,
            'kind': layer.kind,
            'bbox': str(layer.bbox),
            'width': layer.width,
            'height': layer.height,
            'opacity': layer.opacity,
            'text': layer.text,
            'blend_mode': str(layer.blend_mode).replace('Blend', '')
        }
        return output


    def make_serializable(self, data):
        for obj in data:
            if 'artboard' in obj:
                obj['artboard'] = { 'size': str(obj['artboard'].size) }

            if 'blend_mode' in obj:
                obj['blend_mode'] = str(obj['blend_mode'])

            if 'bbox' in obj and type(obj['bbox']) != str:
                obj['bbox'] = str(obj['bbox']) 

            if not obj.get('layers'):
                continue
            
            for layer in obj['layers']:
                for key in layer:
                    if hasattr(layer[key], '__dict__'):
                        replacement = None
                        try:
                            text = layer[key].text
                            replacement = self.parse_text_layer(layer[key])
                        except:
                            replacement = self.parse_non_text_layer(layer[key])
                        layer[key] = replacement
                    elif key == 'info':
                        if 'blend_mode' in layer['info']:
                            layer['info']['blend_mode'] = str(layer['info']['blend_mode'])
        return data


    def read_file(self):
        psd = PSDImage.open(os.path.abspath('./assets/color-theme.psd'))
        return psd


    def clean_output(self, obj):
        str_obj = str(obj)
        result = str_obj.replace("'", '"')
        return result.replace('False', 'false').replace('True', 'true')


    def extract(self):
        # psd = PSDImage.open(file)
        psd = self.read_file()
        
        artboard_info = self.get_artboard_info(psd)

        artboard_data = {}

        if artboard_info:
            artboard_data = self.parse_artboards(artboard_info)
        
        output_dir, layer_info, canvas_width, canvas_height = self.separate_parts(psd)

        serializable_artboards = self.make_serializable(artboard_data)

        serializable_layers = self.make_serializable(layer_info)
        
        response = {
            "artboard_data": serializable_artboards,
            "layer_info": serializable_layers
        }
        output = self.clean_output(response)

        return output
        


        
