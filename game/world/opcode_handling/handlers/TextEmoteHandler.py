from struct import pack, unpack

from network.packet.PacketWriter import *
from network.packet.PacketReader import *
from database.dbc.DbcDatabaseManager import DbcDatabaseManager
from game.world.managers.GridManager import GridManager
from utils.ConfigManager import config
from utils.constants.ObjectCodes import ObjectTypes
from utils.constants.UnitCodes import StandState
from utils.constants.ObjectCodes import Emotes


class TextEmoteHandler(object):

    @staticmethod
    def handle(world_session, socket, reader):
        if world_session.player_mgr.is_alive and len(reader.data) >= 12:
            emote_text_id, guid = unpack('<IQ', reader.data)
            emote = DbcDatabaseManager.emote_text_get_by_id(world_session.dbc_db_session, emote_text_id)

            if emote:
                data = pack('<QI', world_session.player_mgr.guid, emote_text_id)
                target = GridManager.get_surrounding_unit_by_guid(world_session.player_mgr, guid, include_players=True)

                if not target:
                    data += pack('<B', 0)
                elif target.get_type() == ObjectTypes.TYPE_PLAYER:
                    player_name_bytes = PacketWriter.string_to_bytes(target.player.name)
                    data += pack('<%us' % len(player_name_bytes),
                                 player_name_bytes)
                elif target.get_type() == ObjectTypes.TYPE_UNIT and target.creature_template:
                    unit_name_bytes = PacketWriter.string_to_bytes(target.creature_template.name)
                    data += pack('<%us' % len(unit_name_bytes),
                                 unit_name_bytes)
                else:
                    data += pack('<B', 0)

                GridManager.send_surrounding_in_range(PacketWriter.get_packet(OpCode.SMSG_TEXT_EMOTE, data),
                                                      world_session.player_mgr, config.World.Chat.ChatRange.emote_range)

                # Perform visual emote action if needed

                emote_id = emote.EmoteID
                state = StandState.UNIT_STANDING.value

                if emote_text_id == Emotes.SIT.value:
                    if not world_session.player_mgr.is_sitting:
                        state = StandState.UNIT_SITTING.value
                        world_session.player_mgr.stand_state = state
                elif emote_text_id == Emotes.STAND.value:
                    world_session.player_mgr.stand_state = state
                elif emote_text_id == Emotes.SLEEP:
                    if not world_session.player_mgr.stand_state != StandState.UNIT_SLEEPING.value:
                        state = StandState.UNIT_SLEEPING.value
                    world_session.player_mgr.stand_state = state
                elif emote_text_id == Emotes.SLEEP:
                    if not world_session.player_mgr.stand_state != StandState.UNIT_KNEEL.value:
                        state = StandState.UNIT_KNEEL.value
                    world_session.player_mgr.stand_state = state
                else:
                    world_session.player_mgr.play_emote(emote_id)

                # TODO Stand state changes are still not working

        return 0
