from soundtouchbose.api.xml_helpers import build_content_item_xml, build_key_xml, parse_info_xml, parse_presets_xml
from soundtouchbose.core.station_library import Station


def test_build_content_item_xml_escapes_station_name() -> None:
    station = Station(
        identifier="s1",
        name="Rock & Roll",
        category="Rock",
        source="TUNEIN",
        location="/v1/playback/station/s1",
    )

    xml = build_content_item_xml(station)

    assert 'source="TUNEIN"' in xml
    assert "Rock &amp; Roll" in xml
    assert 'location="/v1/playback/station/s1"' in xml


def test_build_key_xml_contains_sender() -> None:
    assert build_key_xml("PRESET_1", "press") == '<key state="press" sender="Gabbo">PRESET_1</key>'


def test_parse_info_xml_reads_expected_fields() -> None:
    xml = """
    <info>
      <name>Wohnzimmer</name>
      <deviceID>123</deviceID>
      <type>SoundTouch 20</type>
      <networkType>wifi</networkType>
      <softwareVersion>1.2.3</softwareVersion>
      <macAddress>AA:BB:CC</macAddress>
    </info>
    """

    parsed = parse_info_xml(xml)

    assert parsed["name"] == "Wohnzimmer"
    assert parsed["type"] == "SoundTouch 20"
    assert parsed["software_version"] == "1.2.3"


def test_parse_presets_xml_extracts_entries() -> None:
    xml = """
    <presets>
      <preset id="1">
        <ContentItem source="TUNEIN" location="/v1/playback/station/s24875">
          <itemName>Deutschlandfunk</itemName>
        </ContentItem>
      </preset>
    </presets>
    """

    parsed = parse_presets_xml(xml)

    assert parsed == [{"id": 1, "name": "Deutschlandfunk", "source": "TUNEIN", "location": "/v1/playback/station/s24875"}]
