from tools.local_preview_render import assign_words_to_spans


def test_words_follow_audio_gaps_not_nearest_scene_centres():
    # Unequal clips: a word near the end of a long clip must not jump to the next scene.
    spans = [(0., 3.), (3.2, 20.), (20.2, 23.)]
    words = [["one", 2.8, 2.9], ["two", 3.3, 3.5], ["warning", 19.6, 19.9], ["comment", 20.3, 20.6]]
    buckets = assign_words_to_spans(words, spans)
    assert [[w[0] for w in group] for group in buckets] == [["one"], ["two", "warning"], ["comment"]]
    assert sum(map(len, buckets)) == len(words)


def test_concat_preserves_24khz_scene_durations(tmp_path):
    import wave
    from tools.local_preview_render import concat, wav_seconds, GAP_S, LEAD_IN_S
    wavs = []
    for i, duration in enumerate((0.7, 1.2)):
        path = tmp_path / f"line{i}.wav"
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
            w.writeframes(b"\0\0" * int(24000 * duration))
        wavs.append(path)
    target = tmp_path / "voice.wav"
    spans = concat(wavs, target)
    assert abs(spans[0][0] - LEAD_IN_S) < .001
    expected = LEAD_IN_S + 0.7 + 1.2 + 2 * GAP_S
    assert abs(wav_seconds(target) - expected) < .01
    with wave.open(str(tmp_path / "lead.wav")) as lead:
        assert lead.getframerate() == 24000
