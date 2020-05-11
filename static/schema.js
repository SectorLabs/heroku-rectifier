window.schema = {
    "type": "object",
    "patternProperties": {
        ".*": {
            "type": "object",
            "patternProperties": {
                "^(?!mode).*$": {
                    "type": "object",
                    "properties": {
                        "intervals": {
                            "type": "array",
                            "items": {
                                "type": "number"
                            }
                        },
                        "workers": {
                            "type": "array",
                            "items": {
                                "type": "number"
                            }
                        },
                        "cooldown": {
                            "type": "number"
                        },
                        "consumers_formation_name": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "intervals",
                        "workers",
                        "cooldown",
                        "consumers_formation_name"
                    ],
                    "additionalProperties": false
                },
                "^mode$": {
                    "type": "string",
                    "enum": [
                        "scale",
                        "noop",
                        "kill"
                    ]
                }
            }
        }
    },
    "additionalProperties": false
};


