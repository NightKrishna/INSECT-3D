from pygltflib import GLTF2, TextureInfo
import json


def convert(input_path, output_path):
    gltf = GLTF2().load(input_path)

    if not gltf.materials:
        print('No materials found')
        gltf.save(output_path)
        return

    for mat in gltf.materials:
        exts = getattr(mat, 'extensions', None)
        if not exts:
            continue

        spec = exts.get('KHR_materials_pbrSpecularGlossiness')
        if not spec:
            continue

        # Ensure pbrMetallicRoughness exists
        if not mat.pbrMetallicRoughness:
            from pygltflib import PbrMetallicRoughness
            mat.pbrMetallicRoughness = PbrMetallicRoughness()

        # Map diffuseFactor -> baseColorFactor
        diffuseFactor = spec.get('diffuseFactor')
        if diffuseFactor:
            mat.pbrMetallicRoughness.baseColorFactor = diffuseFactor

        # Map diffuseTexture -> baseColorTexture
        diffuseTexture = spec.get('diffuseTexture')
        if diffuseTexture and isinstance(diffuseTexture, dict):
            idx = diffuseTexture.get('index')
            if idx is not None:
                mat.pbrMetallicRoughness.baseColorTexture = TextureInfo(index=idx)

        # Set non-metallic defaults
        mat.pbrMetallicRoughness.metallicFactor = 0.0
        # Try set roughness from glossiness if available
        gloss = spec.get('glossinessFactor')
        if gloss is not None:
            mat.pbrMetallicRoughness.roughnessFactor = max(0.0, min(1.0, 1.0 - gloss))
        else:
            mat.pbrMetallicRoughness.roughnessFactor = 1.0

        # Remove the spec-gloss extension from the material
        if 'KHR_materials_pbrSpecularGlossiness' in mat.extensions:
            del mat.extensions['KHR_materials_pbrSpecularGlossiness']

    # Clean top-level extensionsUsed / extensionsRequired
    if gltf.extensionsUsed:
        gltf.extensionsUsed = [e for e in gltf.extensionsUsed if e != 'KHR_materials_pbrSpecularGlossiness']
    if gltf.extensionsRequired:
        gltf.extensionsRequired = [e for e in gltf.extensionsRequired if e != 'KHR_materials_pbrSpecularGlossiness']

    gltf.save(output_path)
    print(f'Wrote converted GLB to {output_path}')


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: convert_specgloss_to_metalrough.py input.glb output.glb')
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
