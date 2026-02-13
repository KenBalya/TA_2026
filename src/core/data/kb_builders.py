# src/core/data/kb_builders.py

from __future__ import annotations
from typing import Any, Dict, Tuple

from core.kb.knowledge_base import KnowledgeBase
from core.ks.types import KSId, KSType, ActionType
from core.rules.drels import DRel, DRelEffectType
from core.runtime.world import Context, WorldState

def build_kb_from_two_videos(video1: Dict[str, Any], video2: Dict[str, Any]) -> Tuple[KnowledgeBase, KSId]:
    kb = KnowledgeBase()

    # Components
    C_MACHINE = kb.add_component("MachineProtos18", "Machine PROTOS 1-8", ["protos 1-8", "mesin protos", "mesin"])
    C_GUARD = kb.add_component("GuardPrinterCover", "Guard Printer Cover", ["guard cover", "printer cover", "penutup printer", "penutup pengaman"])
    C_DIE = kb.add_component("DieRoller", "Die Roller", ["die roller", "roller die", "die roller printer"])
    C_RUBBER = kb.add_component("RubberRoller", "Rubber Roller", ["rubber roller", "roller karet"])
    C_DISTR_CYL_1 = kb.add_component("DistributorCylinder1", "Distributor Cylinder (metallic)", ["silinder distributor metalik", "distributor cylinder metallic"])
    C_DISTR_CYL_2 = kb.add_component("DistributorCylinder2", "Distributor Cylinder (gold)", ["silinder distributor keemasan", "distributor cylinder gold"])
    C_DISTR_ROLLER = kb.add_component("DistributorRoller", "Distributor Roller (red)", ["roller distributor", "roller distributor merah"])
    C_TRANSFER = kb.add_component("TransferRoller", "Transfer Roller", ["roller transfer"])
    C_NOZZLE = kb.add_component("InkNozzleArea", "Ink Nozzle / Printer Area", ["nosel tinta", "area printer", "unit printer"])

    # Tools
    T_S1S = kb.add_tool("S1SButton", "S1S Button", ["s1s", "tombol s1s", "button s1s"])
    T_AQUA = kb.add_tool("AquaDemineral", "Aqua Demineral", ["aqua de mineral", "air demineral", "demineral"])
    T_BRUSH = kb.add_tool("NonMetalBrush", "Non-metal soft brush", ["sikat non logam", "sikat lembut non-logam", "non-metal brush"])
    T_CLOTH = kb.add_tool("DryCloth", "Dry cloth", ["lap kering", "kain lap", "lap putih"])

    # States
    S_OFF = kb.add_state("MachineOff", "Machine is OFF")
    S_GUARD_OPEN = kb.add_state("GuardOpen", "Guard cover is OPEN")
    S_GUARD_CLOSED = kb.add_state("GuardClosed", "Guard cover is CLOSED")
    S_DIE_REMOVED = kb.add_state("DieRollerRemoved", "Die roller removed")
    S_DIE_CLEAN = kb.add_state("DieRollerClean", "Die roller clean")
    S_RR_DRIVES_OFF = kb.add_state("SecondaryDrivesOff", "Secondary drives are OFF")
    S_RUBBER_REMOVED = kb.add_state("RubberRollersRemoved", "Rubber rollers removed")
    S_RUBBER_CLEAN = kb.add_state("RubberRollersClean", "Rubber rollers clean")
    S_READY = kb.add_state("MachineReady", "Machine ready to operate")

    # Procedures
    v1_id = "VID-PROTOS-DIE-ROLLER"
    v2_id = "VID-PROTOS-RUBBER-ROLLER"
    P1 = kb.add_procedure(v1_id, video1["video_title"], video1["video_summary"])
    P2 = kb.add_procedure(v2_id, video2["video_title"], video2["video_summary"])

    # Evidence segments
    v1_seg_ids: Dict[int, KSId] = {}
    for seg in video1["details"]:
        v1_seg_ids[int(seg["segment_id"])] = kb.add_segment(v1_id, seg)

    v2_seg_ids: Dict[int, KSId] = {}
    for seg in video2["details"]:
        v2_seg_ids[int(seg["segment_id"])] = kb.add_segment(v2_id, seg)

    # Example validator: if ctx.mode production -> must be OFF anyway
    def v_requires_off(ctx: Context, world: WorldState):
        if ctx.mode == "production" and not world.has(S_OFF):
            return False, "mode_production_requires_machine_off"
        return True, "ok"

    # Steps procedure 1 (Die Roller)
    kb.add_step(P1, 1, "Ensure machine is OFF", ActionType.ENSURE_OFF,
                target_components=[C_MACHINE], pre=[], post=[S_OFF],
                tools=[], evidence=[v1_seg_ids[2]],
                notes="Ensure PROTOS 1-8 is OFF before maintenance.",
                validators=[v_requires_off])

    kb.add_step(P1, 2, "Open Guard Printer Cover", ActionType.OPEN_COVER,
                target_components=[C_GUARD], pre=[S_OFF], post=[S_GUARD_OPEN],
                tools=[], evidence=[v1_seg_ids[3]],
                notes="Open guard cover to access die roller.")

    kb.add_step(P1, 3, "Remove Die Roller", ActionType.REMOVE_COMPONENT,
                target_components=[C_DIE], pre=[S_OFF, S_GUARD_OPEN], post=[S_DIE_REMOVED],
                tools=[], evidence=[v1_seg_ids[3]],
                notes="Release lock button and rotate knob to remove die roller.")

    kb.add_step(P1, 4, "Clean Die Roller with Aqua Demineral and non-metal brush, then dry", ActionType.CLEAN_COMPONENT,
                target_components=[C_DIE], pre=[S_DIE_REMOVED], post=[S_DIE_CLEAN],
                tools=[T_AQUA, T_BRUSH, T_CLOTH], evidence=[v1_seg_ids[4]],
                notes="Spray Aqua Demineral, brush gently, wipe dry; repeat for other side.")

    kb.add_step(P1, 5, "Reinstall Die Roller", ActionType.REINSTALL_COMPONENT,
                target_components=[C_DIE], pre=[S_DIE_CLEAN], post=[],
                tools=[], evidence=[v1_seg_ids[5]],
                notes="Press lock button and rotate knob until firmly installed.")

    kb.add_step(P1, 6, "Close Guard Printer Cover; machine ready", ActionType.CLOSE_COVER,
                target_components=[C_GUARD], pre=[S_GUARD_OPEN], post=[S_GUARD_CLOSED, S_READY],
                tools=[], evidence=[v1_seg_ids[6]],
                notes="Close cover and lock; machine can be run again.")

    # Steps procedure 2 (Rubber Roller)
    kb.add_step(P2, 1, "Press S1S to turn OFF Secondary Drives; open printer cover", ActionType.PRESS_BUTTON,
                target_components=[C_MACHINE, C_GUARD], pre=[], post=[S_RR_DRIVES_OFF, S_GUARD_OPEN],
                tools=[T_S1S], evidence=[v2_seg_ids[3]],
                notes="Press S1S; then open the printer cover.")

    kb.add_step(P2, 2, "Remove distributor cylinders (2) and distributor roller", ActionType.REMOVE_COMPONENT,
                target_components=[C_DISTR_CYL_1, C_DISTR_CYL_2, C_DISTR_ROLLER],
                pre=[S_RR_DRIVES_OFF, S_GUARD_OPEN], post=[S_RUBBER_REMOVED],
                tools=[], evidence=[v2_seg_ids[4], v2_seg_ids[5], v2_seg_ids[6]],
                notes="Unlock and remove cylinders and distributor roller.")

    kb.add_step(P2, 3, "Remove transfer roller; prepare Aqua Demineral cloth", ActionType.REMOVE_COMPONENT,
                target_components=[C_TRANSFER], pre=[S_RR_DRIVES_OFF, S_GUARD_OPEN],
                post=[S_RUBBER_REMOVED], tools=[T_AQUA, T_CLOTH], evidence=[v2_seg_ids[7]],
                notes="Remove transfer roller; recommended to use Aqua Demineral-damp cloth.")

    kb.add_step(P2, 4, "Clean rollers, ink nozzle area, and printer unit using Aqua Demineral cloth", ActionType.CLEAN_AREA,
                target_components=[C_RUBBER, C_DISTR_CYL_1, C_DISTR_CYL_2, C_DISTR_ROLLER, C_TRANSFER, C_NOZZLE],
                pre=[S_RUBBER_REMOVED], post=[S_RUBBER_CLEAN],
                tools=[T_AQUA, T_CLOTH],
                evidence=[v2_seg_ids[8], v2_seg_ids[9], v2_seg_ids[10], v2_seg_ids[11], v2_seg_ids[12]],
                notes="Wipe thoroughly; includes nozzle surface and printer unit area.")

    kb.add_step(P2, 5, "Reinstall all cleaned rollers and cylinders", ActionType.REINSTALL_MULTIPLE,
                target_components=[C_DISTR_CYL_1, C_DISTR_CYL_2, C_DISTR_ROLLER, C_TRANSFER, C_RUBBER],
                pre=[S_RUBBER_CLEAN], post=[], tools=[],
                evidence=[v2_seg_ids[13], v2_seg_ids[14], v2_seg_ids[15], v2_seg_ids[16], v2_seg_ids[17]],
                notes="Install back in correct order; secure locks.")

    kb.add_step(P2, 6, "Close printer cover; machine ready", ActionType.CLOSE_COVER,
                target_components=[C_GUARD], pre=[S_GUARD_OPEN], post=[S_GUARD_CLOSED, S_READY],
                tools=[], evidence=[v2_seg_ids[18]],
                notes="Close and lock cover; machine ready to operate.")

    # Cloud
    cloud_id = kb.add_cloud("Cloud-PROTOS-1-8-Maintenance", "PROTOS 1-8 Maintenance Procedures", [P1, P2])


    # DR1: maintenance, enforce MachineOff before OPEN/REMOVE/CLEAN/CLEAN_AREA steps
    kb.add_drel(DRel(
        id="DR1",
        description="In maintenance mode, enforce MachineOff before OPEN_COVER / REMOVE_COMPONENT / CLEAN steps",
        condition=lambda ctx, w: ctx.mode == "maintenance",
        effect_type=DRelEffectType.INJECT_STEP_PRECONDITION,
        payload=S_OFF,
    ))

    # DR2: die roller cleaning requires non-metal brush IF tool availability explicitly set
    # Note that DR1 and DR2 will be applied via rule based inference in the next steps if needed
    def v_brush_required(ctx: Context, world: WorldState):
        if not ctx.available_tools:
            return True, "ok"
        return (KSId(KSType.TOOL, "NonMetalBrush") in ctx.available_tools), "non_metal_brush_required"

    kb.add_drel(DRel(
        id="DR2",
        description="Die roller cleaning requires non-metal brush when tool availability is specified",
        condition=lambda ctx, w: True,
        effect_type=DRelEffectType.ADD_VALIDATOR,
        payload=v_brush_required,
        target_step=KSId(KSType.STEP, f"{P1.name}:step4"),
    ))

    return kb, cloud_id
