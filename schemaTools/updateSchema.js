/**
 * Updates the CRD file generating a K8S CRD openAPIV3Schema from a JSON-Schema.
 */

const fs = require('fs');
const yaml = require('js-yaml');
const toOpenApi = require('json-schema-to-openapi-schema');
const $RefParser = require("@apidevtools/json-schema-ref-parser");

// Clean keys in object recursively
function removeKey(obj, keyNames) {
    for (prop in obj) {
        if (keyNames.includes(prop)) {
            delete obj[prop];
        }
        else if (typeof obj[prop] === 'object')
            removeKey(obj[prop], keyNames);
    }
}

function updateCRDFile(crdFilename, jsonSchemaFilename) {
    let jsonSchema = yaml.load(fs.readFileSync(jsonSchemaFilename, 'utf8'));
    let crd = yaml.load(fs.readFileSync(crdFilename, 'utf8'));
    $RefParser.dereference(jsonSchema, (err, schemaDereferenced) => {
        if (err) {
            console.error(err);
        }
        else {
            const openApiSchema = toOpenApi(schemaDereferenced);
            scenarioSchema = openApiSchema.properties.scenarios.items
            removeKey(scenarioSchema, ["additionalProperties", "default"])
            stepSchema = scenarioSchema.properties.steps.items.oneOf
            removeKey(stepSchema, ["description", "type"])
            scenarioSchema.properties.steps.items.oneOf = stepSchema
            scenarioSchema.properties.steps.items.type = "object"
            var validationSchema = {
                "type": "object",
                "required": ["spec"],
                "properties": {
                    "spec": scenarioSchema
                }
            }
            crd.spec.versions[0].schema.openAPIV3Schema = validationSchema
            let yamlStr = yaml.dump(crd);
            fs.writeFileSync(crdFilename, yamlStr, 'utf8');
        }
    })
}

updateCRDFile('../kubernetes/crd.yml', '../powerfulseal/policy/ps-schema.yaml')
