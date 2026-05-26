package mesh

import (
	"testing"
	"time"

	meshpb "github.com/peteedoo/faulty-link-backend/third_party/protobufs/meshtastic"
)

func BenchmarkStoreUpsert(b *testing.B) {
	store := NewStore(5 * time.Minute)
	node := &Node{
		ID:        1234567890,
		ShortName: "TEST",
		LongName:  "Test Node",
		LastHeard: time.Now(),
	}
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		store.UpsertNode(node)
	}
}

func BenchmarkStoreGetNode(b *testing.B) {
	store := NewStore(5 * time.Minute)
	node := &Node{
		ID:        1234567890,
		ShortName: "TEST",
		LongName:  "Test Node",
		LastHeard: time.Now(),
	}
	store.UpsertNode(node)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		store.GetNode(1234567890)
	}
}

func BenchmarkStoreAddTelemetry(b *testing.B) {
	store := NewStore(5 * time.Minute)
	store.UpsertNode(&Node{ID: 1234567890, ShortName: "TEST", LastHeard: time.Now()})
	tele := &Telemetry{
		NodeID:    1234567890,
		Timestamp: time.Now(),
		Battery:   85,
		Voltage:   4.1,
	}
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		store.AddTelemetry(1234567890, tele)
	}
}

func BenchmarkDecodeFromRadio(b *testing.B) {
	decoder := NewDecoder(nil)
	msg := &meshpb.FromRadio{
		PayloadVariant: &meshpb.FromRadio_NodeInfo{
			NodeInfo: &meshpb.NodeInfo{
				Num: 1234567890,
				User: &meshpb.User{
					Id:        "!12345678",
					ShortName: "TEST",
					LongName:  "Test Node",
				},
			},
		},
	}
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		decoder.decodeFromRadio(msg)
	}
}
