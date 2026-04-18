#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "VehicleActor.generated.h"

class UPoseidonBridge;

/**
 * AVehicleActor - actor driven by a ROS 2 nav_msgs/Odometry topic.
 *
 * Placeholder mesh (a cube or imported glTF) whose world transform is
 * updated each frame from the latest message on the subscribed topic.
 * Used for both AUV and SSV; set TopicName in the map (e.g. "/auv/state"
 * or "/ssv/state").
 *
 * SYSTEM_DESIGN.md Section 14.1: Unreal renders vehicles as a consumer
 * of state. It does not own physics. AGENTS.md Rule 1.1 forbids this
 * class from publishing anywhere.
 */
UCLASS(Blueprintable, BlueprintType)
class POSEIDONUE_API AVehicleActor : public AActor
{
    GENERATED_BODY()

public:
    AVehicleActor();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    /** ROS topic to subscribe to. Typically /auv/state or /ssv/state. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Poseidon|Vehicle")
    FString TopicName;

    /** ROS message type name passed to rosbridge. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Poseidon|Vehicle")
    FString MessageType = TEXT("nav_msgs/Odometry");

    /** Uniform scale applied to raw ROS position (meters) before moving the actor. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Poseidon|Vehicle")
    float WorldScale = 100.0f;  // UE world units are cm by default

    /** Root scene component, to be replaced by a static mesh / Blueprint. */
    UPROPERTY(VisibleAnywhere, Category = "Poseidon|Vehicle")
    class USceneComponent* SceneRoot;

private:
    UFUNCTION()
    void HandleBridgeMessage(const FString& JsonPayload);

    UPROPERTY()
    UPoseidonBridge* Bridge = nullptr;

    FVector TargetLocation = FVector::ZeroVector;
    FQuat TargetOrientation = FQuat::Identity;
    bool bHasSample = false;
};
