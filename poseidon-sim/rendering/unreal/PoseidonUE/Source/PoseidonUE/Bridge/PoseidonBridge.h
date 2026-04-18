#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Dom/JsonObject.h"
#include "IWebSocket.h"
#include "PoseidonBridge.generated.h"

/**
 * UPoseidonBridge - ROS 2 <-> UE5 bridge.
 *
 * Implements ADR-0001. Connects to rosbridge_server over WebSocket,
 * subscribes to read-only ROS 2 topics per the allowlist, and
 * dispatches decoded messages to per-topic handlers via delegates.
 *
 * UE cannot publish actuator topics. The rosbridge allowlist (see
 * poseidon-sim/rendering/bridge/rosbridge_server_allowlist.yaml) rejects
 * any attempt to advertise or publish outside the read-only set, so
 * AGENTS.md Rule 1.1 is enforced at the network layer.
 *
 * Lifetime: one bridge per GameInstance. Reconnect with exponential
 * backoff on drop. Messages received on the WebSocket thread are
 * dispatched to the game thread via AsyncTask(ENamedThreads::GameThread).
 */

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnBridgeMessage, const FString&, JsonPayload);

UCLASS(BlueprintType)
class POSEIDONUE_API UPoseidonBridge : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    /** Connect to rosbridge_server. Host defaults to ws://localhost:9090. */
    UFUNCTION(BlueprintCallable, Category = "Poseidon|Bridge")
    void Connect(const FString& ServerUrl);

    /** Subscribe to a ROS topic. Broadcasts FOnBridgeMessage per message. */
    UFUNCTION(BlueprintCallable, Category = "Poseidon|Bridge")
    void Subscribe(const FString& Topic, const FString& MessageType);

    /** Broadcast when any subscribed topic delivers a message. */
    UPROPERTY(BlueprintAssignable, Category = "Poseidon|Bridge")
    FOnBridgeMessage OnMessage;

    /** Whether the WebSocket is currently connected. */
    UFUNCTION(BlueprintPure, Category = "Poseidon|Bridge")
    bool IsConnected() const;

private:
    void OnSocketConnected();
    void OnSocketConnectionError(const FString& Error);
    void OnSocketClosed(int32 StatusCode, const FString& Reason, bool bWasClean);
    void OnSocketMessage(const FString& Message);

    TSharedPtr<IWebSocket> Socket;
    FString CachedServerUrl;
    TArray<TTuple<FString, FString>> PendingSubscriptions;
};
