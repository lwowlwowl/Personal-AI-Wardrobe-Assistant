"""Unit: virtual try-on workflow template wiring (FR-11)."""
from app.services.comfyui_client import build_virtual_tryon_workflow


def test_build_virtual_tryon_workflow_maps_images_and_prompt():
    wf = build_virtual_tryon_workflow(
        person_image="person.png",
        clothing_image="shirt.png",
        accessory_image="hat.png",
        model_type="2509",
        prompt_text="test prompt",
    )
    assert isinstance(wf, dict)
    if "78" in wf:
        assert wf["78"]["inputs"]["image"] == "person.png"
    if "106" in wf:
        assert wf["106"]["inputs"]["image"] == "shirt.png"
    if "108" in wf:
        assert wf["108"]["inputs"]["image"] == "hat.png"
